# import base64
# import json
# import uuid
# from datetime import datetime, timedelta

# from fastapi import HTTPException
# from sqlalchemy.orm import Session

# from src.application.schemas.base import (
#     BookCreateRequest,
#     BookDetail,
#     BookResponse,
#     BookUpdateRequest,
# )
# from src.infrastructure.database.models import Annotation
# from src.infrastructure.external.gcs import GCSClient
# from src.infrastructure.postgres.book.book_dto import BookDTO


# def get_book_file_signed_url(book_id: str, user_id: str, db: Session):
#     book = db.query(BookDTO).filter(BookDTO.id == book_id).first()
#     if not book:
#         raise HTTPException(
#             status_code=404, detail=f"ID {book_id} の書籍が見つかりません"
#         )

#     if not book.file_path:
#         raise HTTPException(
#             status_code=404, detail="この書籍のファイルが見つかりません"
#         )

#     if book.user_id != user_id:
#         raise HTTPException(
#             status_code=403, detail="この書籍へのアクセス権限がありません"
#         )

#     gcs_client = GCSClient()

#     if gcs_client.use_emulator:
#         return book.file_path
#     else:
#         path = book.file_path.replace(
#             f"{gcs_client.get_gcs_url()}/{gcs_client.bucket_name}/", ""
#         )

#         bucket = gcs_client.get_client().bucket(gcs_client.bucket_name)
#         blob = bucket.blob(path)
#         signed_url = (
#             blob.generate_signed_url(
#                 version="v4", expiration=timedelta(minutes=15), method="GET"
#             )
#             if not gcs_client.use_emulator
#             else book.file_path
#         )
#         return str(signed_url)


# def get_all_covers(user_id: str, db: Session):
#     gcs_client = GCSClient()

#     books = db.query(BookDTO).filter(BookDTO.user_id == user_id).all()

#     result = {"success": True, "data": []}

#     for book in books:
#         if not book.cover_path:
#             continue

#         path = book.cover_path.replace(
#             f"{gcs_client.get_gcs_url()}/{gcs_client.bucket_name}/", ""
#         )

#         bucket = gcs_client.get_client().bucket(gcs_client.bucket_name)
#         blob = bucket.blob(path)
#         cover_url = (
#             blob.generate_signed_url(
#                 version="v4", expiration=timedelta(minutes=15), method="GET"
#             )
#             if not gcs_client.use_emulator
#             else book.cover_path
#         )

#         result["data"].append(
#             {"book_id": book.id, "name": book.name, "cover_url": cover_url}
#         )

#     return result


# def all_books(db: Session):
#     books = db.query(BookDTO).filter(BookDTO.deleted_at == None).all()
#     book_list = [
#         BookDetail.model_validate(book, from_attributes=True) for book in books
#     ]
#     return book_list


# def add_book(body: BookCreateRequest, db: Session) -> BookResponse:
#     try:
#         if not body.book_id:
#             book_id = str(uuid.uuid4())
#         else:
#             book_id = body.book_id

#         if not body.book_name:
#             book_name = body.file_name
#         else:
#             book_name = body.book_name

#         file_data = base64.b64decode(body.file_data)
#         gcs_client = GCSClient()

#         bucket = gcs_client.get_client().bucket(gcs_client.bucket_name)
#         epub_blob_name = f"books/{body.user_id}/{book_id}/book.epub"
#         blob = bucket.blob(epub_blob_name)
#         blob.upload_from_string(file_data, content_type="application/epub+zip")

#         file_path = (
#             f"{gcs_client.get_gcs_url()}/{gcs_client.bucket_name}/{epub_blob_name}"
#         )

#         file_size = len(file_data)

#         cover_path = None
#         if body.cover_image and body.cover_image.startswith("data:image/"):
#             try:
#                 image_data = body.cover_image.split(",")[1]
#                 image_binary = base64.b64decode(image_data)

#                 cover_blob_name = f"books/{body.user_id}/{book_id}/cover.jpg"
#                 cover_blob = bucket.blob(cover_blob_name)
#                 cover_blob.upload_from_string(image_binary, content_type="image/jpeg")

#                 cover_path = f"{gcs_client.get_gcs_url()}/{gcs_client.bucket_name}/{cover_blob_name}"
#             except Exception as e:
#                 print(f"カバー画像の保存中にエラーが発生しました: {str(e)}")

#         metadata = {}
#         if body.book_metadata:
#             try:
#                 metadata = json.loads(body.book_metadata)
#             except json.JSONDecodeError:
#                 pass

#         new_book = BookDTO(
#             id=book_id,
#             user_id=body.user_id,
#             name=book_name,
#             file_path=file_path,
#             cover_path=cover_path,
#             size=file_size,
#             book_metadata=metadata,
#             definitions=[],
#             configuration={},
#             author=metadata.get("creator", None),
#         )

#         db.add(new_book)
#         db.commit()
#         db.refresh(new_book)

#         return BookResponse(
#             success=True,
#             data=BookDetail.model_validate(new_book, from_attributes=True),
#             message="書籍が正常に追加されました",
#         )
#     except Exception:
#         db.rollback()


# def update_book(book_id: str, changes: BookUpdateRequest, db: Session) -> None:
#     """書籍情報を更新する処理を行う関数"""
#     try:
#         book = db.query(BookDTO).filter(BookDTO.id == book_id).first()
#         if not book:
#             raise HTTPException(
#                 status_code=404, detail=f"ID {book_id} の書籍が見つかりません"
#             )

#         changes_dict = changes.model_dump(exclude_unset=True)
#         annotations = changes_dict.pop("annotations", None)

#         if changes_dict:
#             for key, value in changes_dict.items():
#                 setattr(book, key, value)

#         if annotations is not None:
#             existing_annotations = (
#                 db.query(Annotation).filter(Annotation.book_id == book_id).all()
#             )
#             existing_ids = {a.id for a in existing_annotations}
#             new_ids = {a.get("id") for a in annotations if a.get("id")}

#             if existing_ids - new_ids:
#                 db.query(Annotation).filter(
#                     Annotation.id.in_(existing_ids - new_ids)
#                 ).delete(synchronize_session=False)

#             to_update = [
#                 a for a in annotations if a.get("id") and a.get("id") in existing_ids
#             ]
#             to_create = [
#                 a
#                 for a in annotations
#                 if not (a.get("id") and a.get("id") in existing_ids)
#             ]

#             for annotation in to_update:
#                 db.query(Annotation).filter(
#                     Annotation.id == annotation.get("id")
#                 ).update(annotation)

#             if to_create:
#                 db.bulk_save_objects([Annotation(**a) for a in to_create])

#         db.commit()

#         return None

#     except Exception as e:
#         db.rollback()
#         print(f"エラーが発生しました: {str(e)}")
#         raise HTTPException(
#             status_code=500, detail=f"書籍の更新中にエラーが発生しました: {str(e)}"
#         )


# def bulk_delete_books(book_ids: list[str], db: Session) -> dict:
#     """複数の書籍を一括削除する処理を行う関数"""
#     if not book_ids:
#         return {"success": True, "deletedIds": [], "count": 0}

#     try:
#         now = datetime.now()
#         existing_books = db.query(BookDTO).filter(BookDTO.id.in_(book_ids)).all()

#         if not existing_books:
#             return {"success": True, "deletedIds": [], "count": 0}

#         existing_ids = [book.id for book in existing_books]
#         mappings = [
#             {
#                 "id": book_id,
#                 "is_deleted": True,
#                 "deleted_at": now,
#             }
#             for book_id in existing_ids
#         ]

#         db.bulk_update_mappings(BookDTO, mappings)

#         gcs_client = GCSClient()
#         bucket = gcs_client.get_client().bucket(gcs_client.bucket_name)

#         for book in existing_books:
#             print("パス", book.file_path)
#             if book.file_path:
#                 file_path = book.file_path.replace(
#                     f"{gcs_client.get_gcs_url()}/{gcs_client.bucket_name}/", ""
#                 )
#                 blob = bucket.blob(file_path)
#                 try:
#                     blob.delete()
#                 except Exception as e:
#                     print(f"書籍ファイルの削除中にエラーが発生しました: {str(e)}")

#             if book.cover_path:
#                 cover_path = book.cover_path.replace(
#                     f"{gcs_client.get_gcs_url()}/{gcs_client.bucket_name}/", ""
#                 )
#                 blob = bucket.blob(cover_path)
#                 try:
#                     blob.delete()
#                 except Exception as e:
#                     print(f"カバー画像の削除中にエラーが発生しました: {str(e)}")
#         db.commit()

#         return {"success": True, "deletedIds": existing_ids, "count": len(existing_ids)}
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=500, detail=f"書籍の一括削除中にエラーが発生しました: {str(e)}"
#         )
