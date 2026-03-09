from abc import ABC, abstractmethod


class ASTNode(ABC):
    """
    Базовый класс для узла абстрактного синтаксического дерева (AST).
    """
    @abstractmethod
    def get_priority(self) -> int:
        """
        Возвращает приоритет операции узла.
        Чем выше число, тем выше приоритет.

        Приоритеты:
            * '+' - 20
            * '-' - 20
            * '*' - 30
            * '/' - 30
            * '^' - 40
            * логарифм - 90
            * унарные функции - 90
            * перменные - 100
            * числа - 100

        Returns:
            int: приоритет операции.
        """
        raise NotImplementedError("Get_priority error")

    @abstractmethod
    def diff(self, diff_variable: str) -> 'ASTNode':
        """
        Вычисляет производную по переменной variable.

        Args:
            diff_variable (str): Переменная по которой нужно взять производную.

        Returns:
            'ASTNode': Производная.
        """
        raise NotImplementedError("Diff error")

    @abstractmethod
    def to_latex(self, parent_priority: int = 0) -> str:
        """
        Преобразует узел в строку LaTeX.
        Сравнивает приоритет узла с приоритетом родителя,
        если приоритет узла меньше, расставляет скобки.

        Args:
            parent_priority (int = 0): приоритет родителя.

        Returns:
            str: строка LaTeX.
        """
        raise NotImplementedError("To_latex error")

    @abstractmethod
    def simplify(self) -> 'ASTNode':
        """
        Упрощает выражение.

        Returns:
            'ASTNode': Упрощенное выражение.
        """
        raise NotImplementedError("Simplify error")

    @abstractmethod
    def copy(self) -> 'ASTNode':
        """
        Возвращает глубокую копию узла.

        Returns:
            'ASTNode': Глубокая копия узла.
        """
        raise NotImplementedError("Copy error")


class Number(ASTNode):
    """
    Класс для чисел.
    """
    def __init__(self, value: str) -> None:
        """
        Args:
            value (str): Число в виде строки.
        """
        self.value = value

    def get_priority(self) -> int:
        return 100

    def diff(self, diff_variable: str) -> 'ASTNode':
        return Number('0')

    def to_latex(self, parent_priority: int = 0) -> str:
        if self.get_priority() < parent_priority:
            return f"({self.value})"

        return self.value

    def simplify(self) -> 'ASTNode':
        return self.copy()

    def copy(self) -> 'ASTNode':
        return Number(self.value)


class Variable(ASTNode):
    """
    Класс для переменных.
    """
    def __init__(self, input_variable: str) -> None:
        """
        Args:
            input_variable (str): Введенная переменная.
        """
        self.input_variable = input_variable

    def get_priority(self) -> int:
        return 100

    def diff(self, diff_variable: str) -> 'ASTNode':
        if self.input_variable == diff_variable:
            return Number('1')
        else:
            return Number('0')

    def to_latex(self, parent_priority: int = 0) -> str:
        if self.get_priority() < parent_priority:
            return f"({self.input_variable})"

        return self.input_variable

    def simplify(self) -> 'ASTNode':
        return self.copy()

    def copy(self) -> 'ASTNode':
        return Variable(self.input_variable)


class Constant(ASTNode):
    """
    Класс для констант.
    """
    def __init__(self, constant_name: str) -> None:
        """
        Args:
            constant_name (str): Константа.
        """
        self.constant_name = constant_name

    def get_priority(self) -> int:
        return 100

    def diff(self, diff_variable: str) -> 'ASTNode':
        return Number('0')

    def to_latex(self, parent_priority: int = 0) -> str:
        constant = self.constant_name

        if constant == "pi":
            constant = "\\pi"

        if self.get_priority() < parent_priority:
            return f"({constant})"

        return constant

    def simplify(self) -> 'ASTNode':
        return self.copy()

    def copy(self) -> 'ASTNode':
        return Constant(self.constant_name)


class Power(ASTNode):
    """
    Класс для степеней.
    """
    def __init__(self, base: 'ASTNode', index: 'ASTNode') -> None:
        """
        Args:
            base ('ASTNode'): Основание степени.
            index ('ASTNode'): Показатель степени.
        """
        self.base = base
        self.index = index

    def get_priority(self) -> int:
        return 40

    def diff(self, diff_variable: str) -> 'ASTNode':
        if isinstance(self.index, (Number, Constant)):
            return BinaryOperation('*',
                                   BinaryOperation('*',
                                                   self.index.copy(),
                                                   Power(self.base.copy(),
                                                         BinaryOperation('-', self.index.copy(), Number('1')))),
                                   self.base.diff(diff_variable))
        elif isinstance(self.base, (Number, Constant)):
            return BinaryOperation('*',
                                   BinaryOperation('*',
                                                   Power(self.base.copy(), self.index.copy()),
                                                   UnaryFunction('ln', self.base.copy())),
                                   self.index.diff(diff_variable))
        else:
            e_index = BinaryOperation('*', self.index.copy(), UnaryFunction('ln', self.base.copy()))

            return BinaryOperation('*', Power(Constant('e'), e_index), e_index.diff(diff_variable))

    def to_latex(self, parent_priority: int = 0) -> str:
        operator_priority = self.get_priority()

        base_latex = self.base.to_latex(parent_priority=operator_priority)
        index_latex = self.index.to_latex(parent_priority=operator_priority)

        result = f"{base_latex}^{index_latex}"

        if operator_priority < parent_priority:
            return f"({result})"

        return result

    def simplify(self) -> 'ASTNode':
        simplified_base = self.base.simplify()
        simplified_index = self.index.simplify()

        if isinstance(simplified_index, Number) and simplified_index.value == '0':
            return Number('1')
        elif isinstance(simplified_base, Number) and simplified_base.value == '0':
            return Number('0')
        elif isinstance(simplified_index, Number) and simplified_index.value == '1':
            return simplified_base
        elif isinstance(simplified_base, Constant) and simplified_base.constant_name == 'e':
            if isinstance(simplified_index, UnaryFunction) and simplified_index.func == 'ln':
                return simplified_index.argument.copy()
            elif isinstance(simplified_index, BinaryOperation) and simplified_index.operator == '*':
                if isinstance(simplified_index.left, UnaryFunction) and simplified_index.left.func == 'ln':
                    return Power(simplified_index.left.argument.copy(), simplified_index.right.copy())
                elif isinstance(simplified_index.right, UnaryFunction) and simplified_index.right.func == 'ln':
                    return Power(simplified_index.right.argument.copy(), simplified_index.left.copy())

        return Power(simplified_base, simplified_index)

    def copy(self) -> 'ASTNode':
        return Power(self.base.copy(), self.index.copy())


class BinaryOperation(ASTNode):
    """
    Класс для бинарных операций.
    """
    # Словарь приоритетов для операций
    PRIORITIES = {
        '+': 20,
        '-': 20,
        '*': 30,
        '/': 30
    }

    def __init__(self, operator: str, left_operand: 'ASTNode', right_operand: 'ASTNode') -> None:
        """
        Args:
            operator (str): Бинарный оператор.
            left_operand ('ASTNode'): Левый операнд.
            right_operand ('ASTNode'): Правый операнд.
        """
        self.operator = operator
        self.left = left_operand
        self.right = right_operand

    def get_priority(self) -> int:
        return self.PRIORITIES.get(self.operator, 0)

    def diff(self, diff_variable: str) -> 'ASTNode':
        if self.operator == '+':
            return BinaryOperation('+', self.left.diff(diff_variable), self.right.diff(diff_variable))
        elif self.operator == '-':
            return BinaryOperation('-', self.left.diff(diff_variable), self.right.diff(diff_variable))
        elif self.operator == '*':
            term1 = BinaryOperation('*', self.left.diff(diff_variable), self.right.copy())
            term2 = BinaryOperation('*', self.left.copy(), self.right.diff(diff_variable))

            return BinaryOperation('+', term1, term2)
        elif self.operator == '/':
            term1 = BinaryOperation('*', self.left.diff(diff_variable), self.right.copy())
            term2 = BinaryOperation('*', self.left.copy(), self.right.diff(diff_variable))

            numerator = BinaryOperation('-', term1, term2)
            denominator = Power(self.right.copy(), Number('2'))

            return BinaryOperation('/', numerator, denominator)
        else:
            raise NotImplementedError(f"Derivative for operator '{self.operator}' is not implemented")

    def to_latex(self, parent_priority: int = 0) -> str:
        operator_priority = self.get_priority()

        left_latex = self.left.to_latex(parent_priority=operator_priority)
        right_latex = self.right.to_latex(parent_priority=operator_priority)

        if self.operator == '/':
            result = f"\\frac{{{left_latex}}}{{{right_latex}}}"
        else:
            result = f"{left_latex}{self.operator}{right_latex}"

        if operator_priority < parent_priority:
            return f"({result})"

        return result

    def simplify(self) -> 'ASTNode':
        simplified_left = self.left.simplify()
        simplified_right = self.right.simplify()

        if self.operator == '+':
            if isinstance(simplified_left, Number) and simplified_left.value == '0':
                return simplified_right

            if isinstance(simplified_right, Number) and simplified_right.value == '0':
                return simplified_left

            if isinstance(simplified_left, Number) and isinstance(simplified_right, Number):
                return Number(str(float(simplified_left.value) + float(simplified_right.value)))
        elif self.operator == '-':
            if isinstance(simplified_right, Number) and simplified_right.value == '0':
                return simplified_left

            if isinstance(simplified_left, Number) and simplified_left.value == '0':
                return BinaryOperation('*', Number('-1'), simplified_right)
        elif self.operator == '*':
            if isinstance(simplified_left, Number) and simplified_left.value == '0':
                return Number('0')

            if isinstance(simplified_right, Number) and simplified_right.value == '0':
                return Number('0')

            if isinstance(simplified_left, Number) and simplified_left.value == '1':
                return simplified_right

            if isinstance(simplified_right, Number) and simplified_right.value == '1':
                return simplified_left
        elif self.operator == '/':
            if isinstance(simplified_left, Number) and simplified_left.value == '0':
                return Number('0')

            if isinstance(simplified_right, Number) and simplified_right.value == '1':
                return simplified_left

            if isinstance(simplified_left, Number) and isinstance(simplified_right, Number):
                return Number(str(float(simplified_left.value) / float(simplified_right.value)))

        return BinaryOperation(self.operator, simplified_left, simplified_right)

    def copy(self) -> 'ASTNode':
        return BinaryOperation(self.operator, self.left.copy(), self.right.copy())


class UnaryFunction(ASTNode):
    """
    Класс для унарных функций.
    """
    def __init__(self, func_name: str, argument: 'ASTNode') -> None:
        """
        Args:
            func_name (str): Имя функции.
            argument ('ASTNode'): Аргумент функции.
        """
        self.func = func_name
        self.argument = argument

    def get_priority(self) -> int:
        return 90

    def diff(self, diff_variable: str) -> 'ASTNode':
        argument_diff = self.argument.diff(diff_variable)

        if self.func == 'exp':
            return BinaryOperation('*',
                                   Power(Constant('e'), self.argument.copy()),
                                   argument_diff)
        elif self.func == 'ln':
            return BinaryOperation('*',
                                   BinaryOperation('/', Number('1'), self.argument.copy()),
                                   argument_diff)
        elif self.func == 'sin':
            return BinaryOperation('*',
                                   UnaryFunction('cos', self.argument.copy()),
                                   argument_diff)
        elif self.func == 'cos':
            return BinaryOperation('*',
                                   BinaryOperation('*',
                                                   Number('-1'),
                                                   UnaryFunction('sin', self.argument.copy())),
                                   argument_diff)
        elif self.func == 'tan':
            return BinaryOperation('*',
                                   BinaryOperation('/',
                                                   Number('1'),
                                                   Power(UnaryFunction('cos', self.argument.copy()),
                                                         Number('2'))),
                                   argument_diff)
        elif self.func == 'cot':
            return BinaryOperation('*',
                                   BinaryOperation('/',
                                                   Number('-1'),
                                                   Power(UnaryFunction('sin', self.argument.copy()),
                                                         Number('2'))),
                                   argument_diff)
        elif self.func == 'sinh':
            return BinaryOperation('*',
                                   UnaryFunction('cosh', self.argument.copy()),
                                   argument_diff)
        elif self.func == 'cosh':
            return BinaryOperation('*',
                                   UnaryFunction('sinh', self.argument.copy()),
                                   argument_diff)
        elif self.func == 'tanh':
            return BinaryOperation('*',
                                   BinaryOperation('-',
                                                   Number('1'),
                                                   Power(UnaryFunction('tanh', self.argument.copy()),
                                                         Number('2'))),
                                   argument_diff)
        elif self.func == 'coth':
            return BinaryOperation('*',
                                   BinaryOperation('-',
                                                   Number('1'),
                                                   Power(UnaryFunction('coth', self.argument.copy()),
                                                         Number('2'))),
                                   argument_diff)
        else:
            raise NotImplementedError(f"Derivative for function '{self.func}' is not implemented")

    def to_latex(self, parent_priority: int = 0) -> str:
        argument_latex = self.argument.to_latex(parent_priority=0)
        result = f"\\{self.func}({argument_latex})"

        if self.get_priority() < parent_priority:
            return f"({result})"

        return result

    def simplify(self) -> 'ASTNode':
        simplified_argument = self.argument.simplify()

        if self.func == 'exp' and isinstance(simplified_argument, UnaryFunction) and simplified_argument.func == 'ln':
            return simplified_argument.argument.simplify().copy()

        if self.func == 'ln' and isinstance(simplified_argument, UnaryFunction) and simplified_argument.func == 'exp':
            return simplified_argument.argument.simplify().copy()

        if self.func == 'sin' and isinstance(simplified_argument, Number) and simplified_argument.value == '0':
            return Number('0')

        if self.func == 'cos' and isinstance(simplified_argument, Number) and simplified_argument.value == '0':
            return Number('1')

        if self.func == 'tan' and isinstance(simplified_argument, Number) and simplified_argument.value == '0':
            return Number('0')

        if self.func == 'sinh' and isinstance(simplified_argument, Number) and simplified_argument.value == '0':
            return Number('0')

        if self.func == 'cosh' and isinstance(simplified_argument, Number) and simplified_argument.value == '0':
            return Number('1')

        if self.func == 'tanh' and isinstance(simplified_argument, Number) and simplified_argument.value == '0':
            return Number('0')

        return UnaryFunction(self.func, simplified_argument)

    def copy(self) -> 'ASTNode':
        return UnaryFunction(self.func, self.argument.copy())
