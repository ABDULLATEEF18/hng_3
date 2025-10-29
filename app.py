
import os
import traceback
import psycopg2.extras
from flask import Flask, request, jsonify, send_file
from db import init_db_pool, get_conn, release_conn
from utils import (
    fetch_countries,
    fetch_exchange_rates,
    compute_estimated_gdp,
    generate_summary_image,
)
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

# Initialize DB pool
init_db_pool()

# -------------------------------
# Helper Functions
# -------------------------------
def db_execute(conn, query, params=None, fetchone=False, fetchall=False):
    """Helper to run queries with optional fetch."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(query, params or ())
    result = None
    if fetchone:
        result = cur.fetchone()
    elif fetchall:
        result = cur.fetchall()
    cur.close()
    return result


def upsert_country(conn, country_obj):
    """
    Insert or update a country by name_normalized (PostgreSQL version).
    """
    sql = """
    INSERT INTO countries
    (name, name_normalized, capital, region, population, currency_code, exchange_rate, estimated_gdp, flag_url, last_refreshed_at)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT (name_normalized)
    DO UPDATE SET
      name = EXCLUDED.name,
      capital = EXCLUDED.capital,
      region = EXCLUDED.region,
      population = EXCLUDED.population,
      currency_code = EXCLUDED.currency_code,
      exchange_rate = EXCLUDED.exchange_rate,
      estimated_gdp = EXCLUDED.estimated_gdp,
      flag_url = EXCLUDED.flag_url,
      last_refreshed_at = EXCLUDED.last_refreshed_at;
    """
    with conn.cursor() as cur:
        cur.execute(sql, (
            country_obj["name"],
            country_obj["name"].lower(),
            country_obj.get("capital"),
            country_obj.get("region"),
            country_obj["population"],
            country_obj.get("currency_code"),
            country_obj.get("exchange_rate"),
            country_obj.get("estimated_gdp"),
            country_obj.get("flag_url"),
            country_obj.get("last_refreshed_at"),
        ))


# -------------------------------
# Routes
# -------------------------------

# POST /countries/refresh
@app.route("/countries/refresh", methods=["POST"])
def refresh_countries():
    conn = get_conn()
    try:
        # fetch data
        try:
            countries = fetch_countries()
        except Exception:
            return jsonify({
                "error": "External data source unavailable",
                "details": "Could not fetch data from REST Countries"
            }), 503

        try:
            exchange_rates = fetch_exchange_rates()
        except Exception:
            return jsonify({
                "error": "External data source unavailable",
                "details": "Could not fetch data from Exchange Rates"
            }), 503

        # Start transaction
        conn.autocommit = False
        cur = conn.cursor()
        last_refreshed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        total = 0

        for c in countries:
            name = c.get("name")
            if not name:
                continue
            capital = c.get("capital")
            region = c.get("region")
            population = c.get("population") or 0
            flag_url = c.get("flag")
            currencies = c.get("currencies") or []

            currency_code = None
            exchange_rate = None
            estimated_gdp = 0

            if currencies:
                first = currencies[0]
                currency_code = first.get("code")
                if currency_code:
                    rate = exchange_rates.get(currency_code) or exchange_rates.get(currency_code.upper()) or exchange_rates.get(currency_code.lower())
                    if rate:
                        exchange_rate = float(rate)
                        estimated_gdp = compute_estimated_gdp(population, exchange_rate)

            country_obj = {
                "name": name,
                "capital": capital,
                "region": region,
                "population": population,
                "currency_code": currency_code,
                "exchange_rate": exchange_rate,
                "estimated_gdp": estimated_gdp,
                "flag_url": flag_url,
                "last_refreshed_at": last_refreshed_at
            }
            upsert_country(conn, country_obj)
            total += 1

        # Update meta table (Postgres-compatible)
        cur.execute("""
            INSERT INTO meta (key_name, value_text)
            VALUES (%s, %s)
            ON CONFLICT (key_name)
            DO UPDATE SET value_text = EXCLUDED.value_text;
        """, ("last_refreshed_at", last_refreshed_at))
        cur.execute("""
            INSERT INTO meta (key_name, value_text)
            VALUES (%s, %s)
            ON CONFLICT (key_name)
            DO UPDATE SET value_text = EXCLUDED.value_text;
        """, ("total_countries", str(total)))
        cur.close()
        conn.commit()

        # generate summary image
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT name, estimated_gdp FROM countries WHERE estimated_gdp IS NOT NULL ORDER BY estimated_gdp DESC LIMIT 5")
        rows = cur.fetchall()
        top5 = [(r["name"], r["estimated_gdp"]) for r in rows]
        cur.close()
        generate_summary_image(total, top5, last_refreshed_at, out_path="cache/summary.png")

        return jsonify({
            "message": "Refresh successful",
            "total_countries": total,
            "last_refreshed_at": last_refreshed_at
        }), 200

    except Exception as e:
        conn.rollback()
        print("❌ ERROR in /countries/refresh:", str(e))
        traceback.print_exc()
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

    finally:
        release_conn(conn)
       # conn.close()


# GET /countries
@app.route("/countries", methods=["GET"])
def list_countries():
    conn = get_conn()
    try:
        region = request.args.get("region")
        currency = request.args.get("currency")
        sort = request.args.get("sort")

        q = "SELECT id, name, capital, region, population, currency_code, exchange_rate, estimated_gdp, flag_url, last_refreshed_at FROM countries"
        conditions = []
        params = []

        if region:
            conditions.append("region = %s")
            params.append(region)
        if currency:
            conditions.append("currency_code = %s")
            params.append(currency)
        if conditions:
            q += " WHERE " + " AND ".join(conditions)

        if sort:
            if sort == "gdp_desc":
                q += " ORDER BY estimated_gdp DESC"
            elif sort == "gdp_asc":
                q += " ORDER BY estimated_gdp ASC"
            elif sort == "name_asc":
                q += " ORDER BY name ASC"
            elif sort == "name_desc":
                q += " ORDER BY name DESC"

        rows = db_execute(conn, q, params, fetchall=True)
        for r in rows:
            if isinstance(r.get("last_refreshed_at"), datetime):
                r["last_refreshed_at"] = r["last_refreshed_at"].replace(microsecond=0).isoformat()
        return jsonify(rows)
    finally:
        release_conn(conn)
        #conn.close()


# GET /countries/:name
@app.route("/countries/<string:name>", methods=["GET"])
def get_country(name):
    conn = get_conn()
    try:
        row = db_execute(conn,
            "SELECT id, name, capital, region, population, currency_code, exchange_rate, estimated_gdp, flag_url, last_refreshed_at FROM countries WHERE name_normalized=%s",
            (name.lower(),),
            fetchone=True
        )
        if not row:
            return jsonify({"error": "Country not found"}), 404
        if isinstance(row.get("last_refreshed_at"), datetime):
            row["last_refreshed_at"] = row["last_refreshed_at"].replace(microsecond=0).isoformat()
        return jsonify(row)
    finally:
        release_conn(conn)
        #conn.close()


# DELETE /countries/:name
@app.route("/countries/<string:name>", methods=["DELETE"])
def delete_country(name):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM countries WHERE name_normalized=%s", (name.lower(),))
        affected = cur.rowcount
        conn.commit()
        cur.close()
        if affected == 0:
            return jsonify({"error": "Country not found"}), 404
        return jsonify({"message": "Country deleted"}), 200
    finally:
        release_conn(conn)
        #conn.close()


# GET /status
@app.route("/status", methods=["GET"])
def status():
    conn = get_conn()
    try:
        tot = db_execute(conn, "SELECT value_text FROM meta WHERE key_name=%s", ("total_countries",), fetchone=True)
        lr = db_execute(conn, "SELECT value_text FROM meta WHERE key_name=%s", ("last_refreshed_at",), fetchone=True)
        total_countries = int(tot["value_text"]) if tot and tot["value_text"] else 0
        last_refreshed_at = lr["value_text"] if lr and lr["value_text"] else None
        return jsonify({"total_countries": total_countries, "last_refreshed_at": last_refreshed_at})
    finally:
        release_conn(conn)
        #conn.close()


# GET /countries/image
@app.route("/countries/image", methods=["GET"])
def serve_image():
    path = "cache/summary.png"
    if os.path.exists(path):
        return send_file(path, mimetype="image/png")
    return jsonify({"error": "Summary image not found"}), 404


# -------------------------------
# Run App
# -------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
