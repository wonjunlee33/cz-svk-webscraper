class ShouldNotHappenException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class CrappyInternetException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class ProbablyDoesNotExistException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


