class User:
    def __init__(self, username: str, school_district: int) -> None:
        self.school_district: int = school_district
        self.display_name: str = ""
        self.class_name: str = ""
        self.username: str = username
        self.student_id: int = -1
        self.avatar_url: str = ""

    def __repr__(self) -> str:
        return f"Eleven {self.display_name}, {self.class_name} (ID: {self.student_id})"
