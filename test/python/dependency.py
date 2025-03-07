import math
from typing import List, Union, Tuple
from decimal import Decimal, getcontext

# Set precision for decimal calculations
getcontext().prec = 28

class MathOperations:
    @staticmethod
    def add(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """Add two numbers."""
        return a + b

    @staticmethod
    def subtract(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """Subtract b from a."""
        return a - b

    @staticmethod
    def multiply(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """Multiply two numbers."""
        return a * b

    @staticmethod
    def divide(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """Divide a by b."""
        if b == 0:
            raise ValueError("Division by zero is not allowed")
        return a / b

    @staticmethod
    def power(base: Union[int, float], exponent: Union[int, float]) -> Union[int, float]:
        """Calculate base raised to the power of exponent."""
        return math.pow(base, exponent)

class AdvancedMath:
    @staticmethod
    def factorial(n: int) -> int:
        """Calculate factorial of n."""
        if n < 0:
            raise ValueError("Factorial is not defined for negative numbers")
        if n == 0 or n == 1:
            return 1
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result

    @staticmethod
    def fibonacci(n: int) -> List[int]:
        """Generate Fibonacci sequence up to nth term."""
        if n < 0:
            raise ValueError("Fibonacci sequence length cannot be negative")
        if n == 0:
            return []
        if n == 1:
            return [0]
        
        sequence = [0, 1]
        while len(sequence) < n:
            sequence.append(sequence[-1] + sequence[-2])
        return sequence

    @staticmethod
    def is_prime(n: int) -> bool:
        """Check if a number is prime."""
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False
        
        for i in range(3, int(math.sqrt(n)) + 1, 2):
            if n % i == 0:
                return False
        return True

    @staticmethod
    def prime_factors(n: int) -> List[int]:
        """Find prime factors of a number."""
        factors = []
        divisor = 2
        
        while n > 1:
            while n % divisor == 0:
                factors.append(divisor)
                n //= divisor
            divisor += 1
            if divisor * divisor > n:
                if n > 1:
                    factors.append(n)
                break
        return factors

class GeometryCalculations:
    @staticmethod
    def circle_area(radius: Union[int, float]) -> float:
        """Calculate area of a circle."""
        if radius < 0:
            raise ValueError("Radius cannot be negative")
        return math.pi * radius * radius

    @staticmethod
    def circle_circumference(radius: Union[int, float]) -> float:
        """Calculate circumference of a circle."""
        if radius < 0:
            raise ValueError("Radius cannot be negative")
        return 2 * math.pi * radius

    @staticmethod
    def rectangle_area(length: Union[int, float], width: Union[int, float]) -> Union[int, float]:
        """Calculate area of a rectangle."""
        if length < 0 or width < 0:
            raise ValueError("Length and width cannot be negative")
        return length * width

    @staticmethod
    def triangle_area(base: Union[int, float], height: Union[int, float]) -> float:
        """Calculate area of a triangle."""
        if base < 0 or height < 0:
            raise ValueError("Base and height cannot be negative")
        return 0.5 * base * height

    @staticmethod
    def sphere_volume(radius: Union[int, float]) -> float:
        """Calculate volume of a sphere."""
        if radius < 0:
            raise ValueError("Radius cannot be negative")
        return (4/3) * math.pi * radius ** 3

class StatisticalOperations:
    @staticmethod
    def mean(numbers: List[Union[int, float]]) -> float:
        """Calculate arithmetic mean of a list of numbers."""
        if not numbers:
            raise ValueError("Cannot calculate mean of empty list")
        return sum(numbers) / len(numbers)

    @staticmethod
    def median(numbers: List[Union[int, float]]) -> float:
        """Calculate median of a list of numbers."""
        if not numbers:
            raise ValueError("Cannot calculate median of empty list")
        
        sorted_numbers = sorted(numbers)
        length = len(sorted_numbers)
        
        if length % 2 == 0:
            return (sorted_numbers[length//2 - 1] + sorted_numbers[length//2]) / 2
        return sorted_numbers[length//2]

    @staticmethod
    def mode(numbers: List[Union[int, float]]) -> List[Union[int, float]]:
        """Calculate mode(s) of a list of numbers."""
        if not numbers:
            raise ValueError("Cannot calculate mode of empty list")
        
        frequency = {}
        for num in numbers:
            frequency[num] = frequency.get(num, 0) + 1
        
        max_frequency = max(frequency.values())
        return [num for num, freq in frequency.items() if freq == max_frequency]

    @staticmethod
    def variance(numbers: List[Union[int, float]]) -> float:
        """Calculate variance of a list of numbers."""
        if len(numbers) < 2:
            raise ValueError("Variance requires at least two numbers")
        
        mean = StatisticalOperations.mean(numbers)
        squared_diff_sum = sum((x - mean) ** 2 for x in numbers)
        return squared_diff_sum / (len(numbers) - 1)

    @staticmethod
    def standard_deviation(numbers: List[Union[int, float]]) -> float:
        """Calculate standard deviation of a list of numbers."""
        return math.sqrt(StatisticalOperations.variance(numbers))

class TrigonometryOperations:
    @staticmethod
    def degrees_to_radians(degrees: Union[int, float]) -> float:
        """Convert degrees to radians."""
        return math.radians(degrees)

    @staticmethod
    def radians_to_degrees(radians: Union[int, float]) -> float:
        """Convert radians to degrees."""
        return math.degrees(radians)

    @staticmethod
    def sin(angle_degrees: Union[int, float]) -> float:
        """Calculate sine of an angle in degrees."""
        return math.sin(math.radians(angle_degrees))

    @staticmethod
    def cos(angle_degrees: Union[int, float]) -> float:
        """Calculate cosine of an angle in degrees."""
        return math.cos(math.radians(angle_degrees))

    @staticmethod
    def tan(angle_degrees: Union[int, float]) -> float:
        """Calculate tangent of an angle in degrees."""
        return math.tan(math.radians(angle_degrees))

class ComplexNumberOperations:
    @staticmethod
    def add_complex(a: complex, b: complex) -> complex:
        """Add two complex numbers."""
        return a + b

    @staticmethod
    def subtract_complex(a: complex, b: complex) -> complex:
        """Subtract two complex numbers."""
        return a - b

    @staticmethod
    def multiply_complex(a: complex, b: complex) -> complex:
        """Multiply two complex numbers."""
        return a * b

    @staticmethod
    def divide_complex(a: complex, b: complex) -> complex:
        """Divide two complex numbers."""
        if b == 0:
            raise ValueError("Division by zero is not allowed")
        return a / b

    @staticmethod
    def complex_magnitude(z: complex) -> float:
        """Calculate magnitude of a complex number."""
        return abs(z)

class MatrixOperations:
    @staticmethod
    def matrix_add(matrix1: List[List[float]], matrix2: List[List[float]]) -> List[List[float]]:
        """Add two matrices."""
        if len(matrix1) != len(matrix2) or len(matrix1[0]) != len(matrix2[0]):
            raise ValueError("Matrices must have same dimensions for addition")
        
        result = []
        for i in range(len(matrix1)):
            row = []
            for j in range(len(matrix1[0])):
                row.append(matrix1[i][j] + matrix2[i][j])
            result.append(row)
        return result

    @staticmethod
    def matrix_scalar_multiply(matrix: List[List[float]], scalar: float) -> List[List[float]]:
        """Multiply matrix by scalar."""
        result = []
        for i in range(len(matrix)):
            row = []
            for j in range(len(matrix[0])):
                row.append(matrix[i][j] * scalar)
            result.append(row)
        return result

    @staticmethod
    def matrix_transpose(matrix: List[List[float]]) -> List[List[float]]:
        """Transpose a matrix."""
        return [[matrix[j][i] for j in range(len(matrix))] 
                for i in range(len(matrix[0]))]

def test_math_functions():
    """Test various mathematical functions."""
    # Basic operations
    assert MathOperations.add(5, 3) == 8
    assert MathOperations.subtract(10, 4) == 6
    assert MathOperations.multiply(6, 7) == 42
    assert MathOperations.divide(15, 3) == 5

    # Advanced math
    assert AdvancedMath.factorial(5) == 120
    assert AdvancedMath.fibonacci(6) == [0, 1, 1, 2, 3, 5]
    assert AdvancedMath.is_prime(17) == True
    assert AdvancedMath.prime_factors(12) == [2, 2, 3]

    # Geometry
    assert abs(GeometryCalculations.circle_area(2) - 12.5663706144) < 1e-10
    assert GeometryCalculations.rectangle_area(4, 5) == 20
    assert GeometryCalculations.triangle_area(6, 8) == 24

    print("All tests passed!")

if __name__ == "__main__":
    test_math_functions()