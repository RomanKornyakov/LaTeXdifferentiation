from enum import Enum
from typing import NoReturn

FUNCTIONS = ['sin', 'cos', 'tan', 'cot', 'sinh', 'cosh', 'tanh', 'coth', 'exp', 'ln', 'log', 'frac']
CONSTANTS = ['pi', 'e']


class TokenType(Enum):
    """
    Доступные типы токенов:
        * NUMBER: Число
        * VARIABLE: Переменная
        * CONSTANT: Константа
        * FUNCTION: Функция
        * OPERATOR: Оператор
        * LPAREN, RPAREN: Левая и правая круглые скобки ()
        * LBRACE, RBRACE: Левая и правая фигурные скобки {}
        * UNDERSCORE: Нижнее подчеркивание _
        * EOF: Конец строки
    """
    NUMBER = "NUMBER"
    VARIABLE = "VARIABLE"
    CONSTANT = "CONSTANT"
    FUNCTION = "FUNCTION"
    OPERATOR = "OPERATOR"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    UNDERSCORE = "UNDERSCORE"
    EOF = "EOF"


class Token:
    """
    Класс для токенов.
    """
    def __init__(self, token_type: TokenType, value: str) -> None:
        """
        Args:
            token_type (TokenType): Тип токена.
            value (str): Значение токена.
        """
        self.token_type = token_type
        self.value = value

    def __repr__(self) -> str:
        return f"{self.token_type.value}({self.value})"


class Tokenizer:
    """
    Класс для токенизатора.
    """
    def __init__(self, text: str) -> None:
        """
        Инициализирует позицию указателя с 0, список токенов, входной текст и его длину.

        Args:
            text (str): Строка LaTeX для токенизации.
        """
        self.text = text
        self.length = len(text)
        self.pos = 0
        self.tokens = []

    def _current_char(self) -> str | None:
        """
        Возвращает текущий символ по позиции pos.

        Returns:
            str: Текущий символ.
            None: Если строка закончилась.
        """
        if self.pos < self.length:
            return self.text[self.pos]

        return None

    def _peek(self, offset: int = 1) -> str | None:
        """
        Просмотр на offset символов вперёд, не двигая pos. Нужно для предпросмотра.

        Args:
            offset (int): На сколько символов вперёд смотреть (по умолчанию 1).

        Returns:
            str: Символ по позиции pos + offset.
            None: Если строка закончилась.
        """
        pos_ahead = self.pos + offset

        if pos_ahead < self.length:
            return self.text[pos_ahead]

        return None

    def _advance(self) -> None:
        """
        Сдвиг позиции на один символ вперёд.
        """
        self.pos += 1

    def _is_at_end(self) -> bool:
        """
        Проверка - достигли ли конца строки.
        """
        return self.pos >= self.length

    def _skip_whitespace(self) -> None:
        """
        Пропускает все пробельные символы.
        """
        while True:
            current_char = self._current_char()
            if current_char and current_char.isspace():
                self._advance()
            else:
                return

    def _read_number(self) -> Token:
        """
        Читаем число (целое или с точкой).

        Returns:
            Token: Токен типа NUMBER.
        """
        result = ""

        while True:
            current_char = self._current_char()
            if current_char.isdigit():
                result += current_char

                self._advance()
                continue
            elif current_char == "." and self._peek() and self._peek().isdigit():
                result += "."

                self._advance()
                continue
            else:
                break

        return Token(TokenType.NUMBER, result)

    def _read_function(self) -> Token:
        """
        Читаем команду LaTeX после \.
        Выбрасывает ошибку, если первый символ не \ или если функия неизвестна.

        Returns:
            Token: Токен типа FUNCTION или CONSTANT.
        """
        current_char = self._current_char()
        if current_char != "\\":
            self._error("Ожидался \\")

        self._advance()

        result = ""

        while True:
            current_char = self._current_char()
            if current_char and current_char.isalpha():
                result += current_char

                self._advance()
                continue
            else:
                break

        if result == "":
            self._error("Пустое имя функции")

        full_func_name = "\\" + result

        if result in CONSTANTS:
            return Token(TokenType.CONSTANT, full_func_name)
        elif result in FUNCTIONS:
            return Token(TokenType.FUNCTION, full_func_name)
        else:
            self._error(f"Неизвестная функция \\{result}")

    def _read_variable(self) -> Token:
        """
        Читаем одну латинскую букву (переменную или константу e).
        Выбрасывает ошибку, если символ не буква.

        Returns:
            Token: Токен типа VARIABLE или CONSTANT.
        """
        current_char = self._current_char()
        if not current_char or not current_char.isalpha():
            self._error("Ожидалась буква")

        self._advance()

        if current_char == "e":
            return Token(TokenType.CONSTANT, "e")
        else:
            return Token(TokenType.VARIABLE, current_char)

    def _error(self, message: str) -> NoReturn:
        """
        Выброс понятного исключения с позицией ошибки.
        """
        raise ValueError(f"{message} на позиции {self.pos}")

    def tokenize(self) -> list[Token]:
        """
        Основная функция токенизации.

        Returns:
            list[Token]: Список токенов.
        """
        while not self._is_at_end():
            self._skip_whitespace()

            if self._is_at_end():
                break

            current_char = self._current_char()
            if current_char == "\\":
                token = self._read_function()
            elif current_char.isdigit():
                token = self._read_number()
            elif current_char.isalpha():
                token = self._read_variable()
            elif current_char in "+-*/^":
                token = Token(TokenType.OPERATOR, current_char)

                self._advance()
            elif current_char in "(){}":
                bracket_map = {
                    "(": TokenType.LPAREN,
                    ")": TokenType.RPAREN,
                    "{": TokenType.LBRACE,
                    "}": TokenType.RBRACE
                }

                token = Token(bracket_map[current_char], current_char)

                self._advance()
            elif current_char == "_":
                token = Token(TokenType.UNDERSCORE, current_char)

                self._advance()
            else:
                self._error("Неизвестный символ")

            self.tokens.append(token)

        eof_token = Token(TokenType.EOF, "")
        self.tokens.append(eof_token)

        return self.tokens
