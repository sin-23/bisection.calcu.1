from flask import Flask, render_template, request
import math, re
import sympy as sp

app = Flask(__name__)


def create_function_from_string(func_str):
    """
    Converts a raw function string into a callable function f(x).
    Expected input example: "3x3-15x2-20x+50" (which represents 3*x**3 - 15*x**2 - 20*x + 50).

    The function performs these steps:
    1. Insert an explicit multiplication sign between a digit and 'x'.
       E.g., "3x" becomes "3*x".
    2. Convert occurrences where 'x' is immediately followed by digits into exponentiation.
       E.g., "x3" becomes "x**3".
    """
    if not func_str.strip():
        raise Exception("Function input is empty.")
    # Insert explicit multiplication: digit followed immediately by 'x'
    func_str = re.sub(r'(\d)(x)', r'\1*x', func_str)
    # Convert pattern "x" followed by digits to "x**digits"
    func_str = re.sub(r'(x)(\d+)', r'\1**\2', func_str)
    # For safety, remove any curly braces (if present)
    func_str = func_str.replace("{", "(").replace("}", ")")
    try:
        expr = sp.sympify(func_str)
    except Exception as e:
        raise Exception("Error converting expression: " + str(e))
    x = sp.symbols('x')
    f = sp.lambdify(x, expr, modules="math")
    return f


def bisection_method(f, XL, XU, tol=1.0, decimals=4, max_iter=100):
    if f(XL) * f(XU) >= 0:
        return None, "f(XL) and f(XU) must have opposite signs.", []
    iterations = []
    previous_Xr = None
    for i in range(1, max_iter + 1):
        Xr = (XL + XU) / 2.0
        f_XL = f(XL)
        f_Xr = f(Xr)
        if previous_Xr is None:
            ea = None
        else:
            ea = abs((Xr - previous_Xr) / Xr) * 100
        iterations.append({
            "iter": i,
            "XL": XL,
            "XU": XU,
            "Xr": Xr,
            "f(XL)": f_XL,
            "f(Xr)": f_Xr,
            "ea": ea
        })
        if f_Xr == 0:
            return Xr, None, iterations
        if previous_Xr is not None and ea is not None:
            if tol == 0:
                if round(ea, decimals) == 0:
                    return Xr, None, iterations
            else:
                if ea <= tol:
                    return Xr, None, iterations
        if f(XL) * f_Xr < 0:
            XU = Xr
        else:
            XL = Xr
        previous_Xr = Xr
    return Xr, None, iterations


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    iterations = None

    # Default values for form fields.
    func_value = ""
    a_value = ""
    b_value = ""
    tol_value = ""
    decimals_value = ""

    if request.method == "POST":
        # Retrieve the function string from the text input
        func_value = request.form.get("func", "").strip()
        if not func_value:
            func_value = "3x3-15x2-20x+50"  # default value if empty
        a_value = request.form.get("a", "").strip()
        b_value = request.form.get("b", "").strip()
        tol_value = request.form.get("tol", "").strip()
        decimals_value = request.form.get("decimals", "").strip()
        try:
            XL = float(a_value)
            XU = float(b_value)
        except ValueError:
            error = "Invalid numerical input for bounds."
            return render_template("index.html", error=error, func_value=func_value,
                                   a_value=a_value, b_value=b_value, tol_value=tol_value,
                                   decimals_value=decimals_value, result=result, iterations=iterations)
        tol = float(tol_value) if tol_value else 1.0
        decimals = int(decimals_value) if decimals_value else 4
        try:
            f = create_function_from_string(func_value)
            result, error, iterations = bisection_method(f, XL, XU, tol, decimals)
        except Exception as e:
            error = "Error evaluating function: " + str(e)
    return render_template("index.html", result=result, error=error,
                           iterations=iterations, func_value=func_value,
                           a_value=a_value, b_value=b_value, tol_value=tol_value,
                           decimals_value=decimals_value)


if __name__ == "__main__":
    app.run(debug=True)
