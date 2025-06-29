from app import app
from flask import render_template, redirect, url_for, request
from app.forms import ExtractForm
from app.models import Product
import os
import json
from flask import send_file, abort
import pandas as pd
from io import BytesIO
import matplotlib.pyplot as plt
import io
import base64


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
    opinions_path = f"app/data/opinions/{product_id}.json"
    product_path = f"app/data/products/{product_id}.json"

    if not (os.path.exists(opinions_path) and os.path.exists(product_path)):
        return abort(404)

    with open(opinions_path, encoding="utf-8") as f:
        opinions = json.load(f)

    with open(product_path, encoding="utf-8") as f:
        product_info = json.load(f)

    return render_template("product.html", product_id=product_id, product=product_info, opinions=opinions)

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


@app.route("/product/<product_id>/charts")
def charts(product_id):
    product = Product(product_id)
    product.import_info()

    recommendation_data = product.stats.get("recommendations", {})
    labels = ["Not Recommended", "Recommended", "No Opinion"]
    values = [
        recommendation_data.get("false", 0),
        recommendation_data.get("true", 0),
        recommendation_data.get("null", 0)
    ]

    fig1, ax1 = plt.subplots()
    ax1.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
    ax1.axis('equal')
    pie_chart = io.BytesIO()
    plt.savefig(pie_chart, format='png')
    pie_chart.seek(0)
    pie_chart_url = base64.b64encode(pie_chart.getvalue()).decode()

    plt.close(fig1)

    stars_data = product.stats.get("stars", {})
    star_labels = list(map(str, stars_data.keys()))
    star_values = list(stars_data.values())

    fig2, ax2 = plt.subplots()
    ax2.bar(star_labels, star_values, color='skyblue')
    ax2.set_xlabel("Stars")
    ax2.set_ylabel("Number of Opinions")
    ax2.set_title("Number of Opinions by Star Rating")
    bar_chart = io.BytesIO()
    plt.savefig(bar_chart, format='png')
    bar_chart.seek(0)
    bar_chart_url = base64.b64encode(bar_chart.getvalue()).decode()

    plt.close(fig2)

    return render_template("charts.html",
        product_id=product_id,
        pie_chart_url=pie_chart_url,
        bar_chart_url=bar_chart_url)