from app import app
from flask import render_template, redirect, url_for, request
from app.forms import ExtractForm
from app.models import Product
import os
import json
from flask import send_file, abort
import pandas as pd

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
    products_data = []
    products_dir = "./app/data/products"
    if os.path.exists(products_dir):
        for filename in os.listdir(products_dir):
            if filename.endswith(".json"):
                with open(os.path.join(products_dir, filename), encoding="utf-8") as f:
                    product_data = json.load(f)
                    products_data.append(product_data)
    return render_template("products.html", products=products_data)

@app.route("/product/<product_id>")
def product(product_id):
    return render_template("product.html", product_id=product_id)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/download/<product_id>/<file_type>")
def download_opinions(product_id, file_type):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    opinions_dir = os.path.join(base_dir, "data", "opinions")
    json_path = os.path.join(opinions_dir, f"{product_id}.json")

    if not os.path.exists(json_path):
        return abort(404, description="Opinions not found")

    with open(json_path, encoding="utf-8") as f:
        opinions_data = json.load(f)

    df = pd.DataFrame(opinions_data)

    if file_type == "json":
        return send_file(json_path, as_attachment=True)
    
    elif file_type == "csv":
        csv_path = os.path.join(opinions_dir, f"{product_id}.csv")
        df.to_csv(csv_path, index=False)
        return send_file(csv_path, as_attachment=True)

    elif file_type == "xlsx":
        xlsx_path = os.path.join(opinions_dir, f"{product_id}.xlsx")
        df.to_excel(xlsx_path, index=False)
        return send_file(xlsx_path, as_attachment=True)

    else:
        return abort(400, description="Invalid file type")