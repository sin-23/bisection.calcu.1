from flask import Flask, render_template, request, redirect, url_for, session
import math, re, os
import sympy as sp

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generates a random secret key each time

def create_function_from_string(func_str, angle_mode="radians"):
    """
    Converts a raw function string into a callable function f(x).
    Supports both plain text and LaTeX input.
    """
    if not func_str.strip():
        raise Exception("Function input is empty.")

    # If the input contains a backslash, assume it's LaTeX format.
    if "\\" in func_str:
        try:
            from sympy.parsing.latex import parse_latex
        except ImportError:
            raise Exception("LaTeX parsing requires sympy.parsing.latex and additional dependencies.")
        try:
            expr = parse_latex(func_str)
        except Exception as e:
            raise Exception("Error converting LaTeX expression: " + str(e))
    else:
        # Process non-LaTeX input.
        func_str = re.sub(r'(\d)(x)', r'\1*x', func_str)
        func_str = re.sub(r'(x)(\d+)', r'\1**\2', func_str)
        func_str = func_str.replace("{", "(").replace("}", ")")
        try:
            expr = sp.sympify(func_str)
        except Exception as e:
            raise Exception("Error converting expression: " + str(e))

    x = sp.symbols('x')

    if angle_mode == "degrees":
        # Use string keys so that the trig functions in the expression are properly replaced.
        trig_functions = {
            "sin": lambda x: math.sin(math.radians(x)),
            "cos": lambda x: math.cos(math.radians(x)),
            "tan": lambda x: math.tan(math.radians(x)),
            "asin": lambda x: math.degrees(math.asin(x)),
            "acos": lambda x: math.degrees(math.acos(x)),
            "atan": lambda x: math.degrees(math.atan(x))
        }
        f = sp.lambdify(x, expr, modules=[trig_functions, "math"])
    else:
        f = sp.lambdify(x, expr, modules="math")
    return f

def bisection_method(f, XL, XU, tol=1.0, decimals=4, max_iter=100):
    # Set a warning if the initial limits are “invalid” (i.e. no sign change)
    warning = None
    if f(XL) * f(XU) >= 0:
        warning = "Warning: The provided limits may be invalid because f(XL) and f(XU) do not have opposite signs."

    iterations = []
    previous_Xr = None
    for i in range(1, max_iter + 1):
        Xr = (XL + XU) / 2.0
        f_XL = f(XL)
        f_Xr = f(Xr)
        if previous_Xr is None:
            ea = None
        else:
            if Xr != 0:
                ea = abs((Xr - previous_Xr) / Xr) * 100
            else:
                ea = None
        iterations.append({
            "iter": i,
            "XL": XL,
            "XU": XU,
            "Xr": Xr,
            "f(XL)": f_XL,
            "f(Xr)": f_Xr,
            "ea": ea
        })
        if abs(f_Xr) < 1e-12:
            return Xr, warning, iterations

        # Stop iterating when the relative error is below or equal to the user-specified tolerance.
        if previous_Xr is not None and ea is not None and ea <= tol:
            return Xr, warning, iterations

        if f(XL) * f_Xr < 0:
            XU = Xr
        else:
            XL = Xr
        previous_Xr = Xr
    return Xr, warning, iterations

# Custom filter to format numbers with superscript exponent if in scientific notation.
@app.template_filter('sup_format')
def sup_format(value, decimals=6):
    try:
        value = float(value)
        # Use general formatting to potentially get scientific notation.
        formatted = f"{value:.{decimals}g}"
        if "e" in formatted:
            base, exp = formatted.split("e")
            exp = int(exp)
            return f"{base}×10<sup>{exp}</sup>"
        else:
            # If not in scientific notation, use fixed-point format.
            return f"{value:.{decimals}f}"
    except Exception:
        return value

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Retrieve form values
        func_value = request.form.get("func_hidden", "").strip()
        if not func_value:
            func_value = "3x3-15x2-20x+50"  # default function if empty
        a_value = request.form.get("a", "").strip()
        b_value = request.form.get("b", "").strip()
        tol_value = request.form.get("tol", "").strip()
        decimals_value = request.form.get("decimals", "").strip()
        angle_mode = request.form.get("angleMode", "radians")

        try:
            XL = float(a_value)
            XU = float(b_value)
        except ValueError:
            session["error"] = "Invalid numerical input for bounds."
            session["result"] = None
            session["iterations"] = None
            session["warning"] = None
            session["angleMode"] = angle_mode
            # Retain the values so they appear in the form.
            session["func_value"] = func_value
            session["a_value"] = a_value
            session["b_value"] = b_value
            session["tol_value"] = tol_value
            session["decimals_value"] = decimals_value
            return redirect(url_for('index'))

        tol = float(tol_value) if tol_value else 1.0
        decimals = int(decimals_value) if decimals_value else 4

        try:
            f = create_function_from_string(func_value, angle_mode)
            result, warning, iterations = bisection_method(f, XL, XU, tol, decimals)
            error = None
        except Exception as e:
            error = "Error evaluating function: " + str(e)
            result = None
            iterations = None
            warning = None

        # Store results in session along with the input values so they are retained.
        session["result"] = result
        session["error"] = error
        session["warning"] = warning
        session["iterations"] = iterations
        session["angleMode"] = angle_mode
        session["func_value"] = func_value
        session["a_value"] = a_value
        session["b_value"] = b_value
        session["tol_value"] = tol_value
        session["decimals_value"] = decimals_value

        return redirect(url_for('index'))

    else:
        # On GET, pop any stored values so they appear only once.
        result = session.pop("result", None)
        error = session.pop("error", None)
        warning = session.pop("warning", None)
        iterations = session.pop("iterations", None)
        angle_mode = session.pop("angleMode", "radians")
        func_value = session.pop("func_value", "")
        a_value = session.pop("a_value", "")
        b_value = session.pop("b_value", "")
        tol_value = session.pop("tol_value", "")
        decimals_value = session.pop("decimals_value", "")
        return render_template("index.html", result=result, error=error, warning=warning, iterations=iterations,
                               func_value=func_value, a_value=a_value, b_value=b_value,
                               tol_value=tol_value, decimals_value=decimals_value, angleMode=angle_mode)

if __name__ == "__main__":
    app.run(debug=True)
