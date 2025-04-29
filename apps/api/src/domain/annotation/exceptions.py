class AnnotationNotFoundError(Exception):
    """指定されたアノテーションが見つからない場合に送出される例外"""

    def __init__(self, annotation_id: str) -> None:
        self.annotation_id = annotation_id
        super().__init__(f"Annotation with id '{annotation_id}' not found.")
