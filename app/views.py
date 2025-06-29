from app import app
from flask import render_template, redirect, url_for, request
from app.forms import ExtractForm
from app.models import Product
import os
import json
from flask import send_file, abort
import pandas as pd
from io import BytesIO

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/extract")
def render_form():
    form = ExtractForm()
    return render_template("extract.html", form=form)

@app.route("/extract", methods=['POST'])
def extract():
    form = ExtractForm(request.form)
    if form.validate():
        product_id = form.product_id.data
        product = Product(product_id)
        if product.extract_name():
            product.extract_opinions()
            product.analyze()
            product.export_info()
            product.export_opinions()
            return redirect(url_for('product', product_id=product_id))
        form.product_id.errors.append('There is no product for provided id or product has no opinions')
        return render_template('extract.html', form=form)
    return render_template('extract.html', form=form)

@app.route("/products")
def products():
    import os, json
    from app.models import Product

    products_dir = os.path.join(os.path.dirname(__file__), "data", "products")
    product_files = [f for f in os.listdir(products_dir) if f.endswith(".json")]
    
    products = []

    for filename in product_files:
        with open(os.path.join(products_dir, filename), encoding="utf-8") as f:
            data = json.load(f)
            products.append({
                "product_id": data["product_id"],
                "product_name": data["product_name"],
                "opinions_count": data["stats"].get("opinions_count", 0),
                "pros_count": data["stats"].get("pros_count", 0),
                "cons_count": data["stats"].get("cons_count", 0),
                "average_score": data["stats"].get("average_rate", 0)
            })

    return render_template("products.html", products=products)

@app.route("/product/<product_id>")
def product(product_id):
    return render_template("product.html", product_id=product_id)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/download/<product_id>/<file_type>")
def download_opinions(product_id, file_type):
    opinions_path = os.path.join("app", "data", "opinions", f"{product_id}.json")
    
    if not os.path.exists(opinions_path):
        return abort(404, description="Opinions not found")

    with open(opinions_path, encoding="utf-8") as f:
        opinions = json.load(f)

    if not opinions:
        return abort(404, description="No opinions to export")

    df = pd.DataFrame(opinions)

    if file_type == "json":
        output = BytesIO()
        output.write(json.dumps(opinions, indent=4, ensure_ascii=False).encode("utf-8"))
        output.seek(0)
        return send_file(output, as_attachment=True, download_name=f"{product_id}.json", mimetype="application/json")

    elif file_type == "csv":
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return send_file(output, as_attachment=True, download_name=f"{product_id}.csv", mimetype="text/csv")

    elif file_type == "xlsx":
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        return send_file(output, as_attachment=True, download_name=f"{product_id}.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    return abort(400, description="Unsupported file format")