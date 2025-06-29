import datetime

from fastapi import UploadFile, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload

from app.dto.response.ReviewResponseSchemas import ReviewCreate, ReviewDetail
from app.models import Review, User
from app.util.azure_upload import upload_file_to_azure, get_full_azure_url, validate_image_upload


def get_review_details_in_photo_studio(db: Session, ps_id: int, offset: int, limit: int):
    try:
        sql = text("""
        SELECT
            r.review_id,
            r.rating,
            r.content,
            r.image_url,
            r.created_at,
            u.nick_name AS user_nickname
        FROM review r
        INNER JOIN user u ON r.user_id = u.user_id
        WHERE r.ps_id = :ps_id
        ORDER BY r.created_at DESC
        LIMIT :limit OFFSET :offset
        """)

        result = db.execute(sql, {
            "ps_id": ps_id,
            "limit": limit,
            "offset": offset
        }).mappings().all()

        count_sql = text("SELECT COUNT(*) FROM review WHERE ps_id = :ps_id")
        total = db.execute(count_sql, {"ps_id": ps_id}).scalar()

        items = []
        # 이미지 URL에 전체 경로 붙이기
        for row in result:
            row_dict = dict(row)
            if row_dict["image_url"]:
                row_dict["image_url"] = get_full_azure_url(row_dict["image_url"])
            items.append(row_dict)

        return {
            "items": items,
            "total": total,
            "offset": offset,
            "limit": limit,
            "has_more": offset + len(result) < total
        }
    except Exception as e:
        print(f"리뷰 목록 조회 시 에러 발생: {e}")
        return {
            "items": [],
            "total": 0,
            "offset": offset,
            "limit": limit,
            "has_more": False
        }

# 리뷰 등록
def create_review(db: Session, data: ReviewCreate, user_email: str, image_file: UploadFile):

    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    user_id = user.user_id

    image_url = None

    if image_file and image_file != "":
        validate_image_upload(image_file)

        try:
            image_filename = upload_file_to_azure(image_file)
            image_url = image_filename # DB에 저장
        except Exception as e:
            raise HTTPException(status_code=500, detail="이미지 업로드 실패: " + str(e))

    review = Review(
        rating=data.rating,
        content=data.content,
        image_url=image_url,
        user_id=user_id,
        ps_id=data.ps_id
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    full_image_url = get_full_azure_url(image_url) if image_url else None

    return {
        "review_id": review.review_id,
        "rating": review.rating,
        "content": review.content,
        "image_url": full_image_url,
        "created_at": review.created_at,
        "updated_at": review.updated_at,
        "user_id": review.user_id,
        "ps_id": review.ps_id,
    }


def a_review_detail(db, ps_id, review_id):
    review = (
        db.query(Review)
        .options(joinedload(Review.writer))
        .filter(Review.review_id == review_id)
        .first()
    )

    if not review or review.ps_id != ps_id:
        raise HTTPException(404, "리뷰를 찾을 수 없습니다")

    return ReviewDetail(
        review_id= review.review_id,
        rating= review.rating,
        content= review.content,
        image_url= get_full_azure_url(review.image_url) if review.image_url else None,
        created_at= review.created_at,
        updated_at= review.updated_at,
        user_id= review.user_id,
        user_nickname= review.writer.nick_name,
        user_profile= review.writer.profile_image,
        ps_id= review.ps_id,
        name= review.studio.ps_name,
    )