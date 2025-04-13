class AnnotationError(Exception):
    pass


class AnnotationNotFoundError(AnnotationError):
    def __init__(self, annotation_id: str | None = None) -> None:
        self.annotation_id = annotation_id
        message = f"Annotation not found: {annotation_id}" if annotation_id else "Annotation not found"
        super().__init__(message)
