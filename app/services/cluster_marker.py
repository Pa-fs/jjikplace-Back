from sqlalchemy import text
from sqlalchemy.orm import Session

def get_filtered_markers(db: Session, sw_lat: float, sw_lng: float, ne_lat: float, ne_lng: float, category=None):
    if category:
        sql = text("""
        SELECT
            ps.ps_id AS id,
            ps.ps_name AS name,
            ps.lat,
            ps.lng,
            ps.road_addr,
            COALESCE(ROUND(AVG(r.rating), 1), 0) AS review_avg_score,
            COUNT(r.review_id) AS review_cnt
        FROM photo_studios ps
        INNER JOIN photo_studio_category psc ON ps.ps_id = psc.ps_id
        INNER JOIN category c ON psc.category_id = c.category_id
        LEFT JOIN review r ON r.ps_id = ps.ps_id
        WHERE c.name = :category
          AND CAST(ps.lat AS FLOAT) BETWEEN :sw_lat AND :ne_lat
          AND CAST(ps.lng AS FLOAT) BETWEEN :sw_lng AND :ne_lng
        GROUP BY ps.ps_id
        """)

        params = {
            "sw_lat": sw_lat,
            "ne_lat": ne_lat,
            "sw_lng": sw_lng,
            "ne_lng": ne_lng,
            "category": category,
        }
    else:
        sql = text("""
        SELECT
            ps.ps_id AS id,
            ps.ps_name AS name,
            ps.lat,
            ps.lng,
            ps.road_addr,
            COALESCE(ROUND(AVG(r.rating), 1), 0) AS review_avg_score,
            COUNT(r.review_id) AS review_cnt
        FROM photo_studios ps
        LEFT JOIN review r ON ps.ps_id = r.ps_id
        WHERE CAST(ps.lat AS FLOAT) BETWEEN :sw_lat AND :ne_lat
          AND CAST(ps.lng AS FLOAT) BETWEEN :sw_lng AND :ne_lng
        GROUP BY ps.ps_id
        """)
        params = {
            "sw_lat": sw_lat,
            "ne_lat": ne_lat,
            "sw_lng": sw_lng,
            "ne_lng": ne_lng,
        }

    result = db.execute(sql, params).mappings().all()

    return {
        "level": "marker",
        "markers": result
    }