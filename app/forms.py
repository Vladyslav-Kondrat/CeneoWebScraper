from wtforms import Form, StringField, SubmitField, validators

class ExtractForm(Form):
    product_id = StringField("Product id", name="product_id", id="product_id", validators=(
        validators.DataRequired(message="Prooduct ID i required"),
        validators.Length(min=6, max=10, message = "Product ID should hv=ave between 6 and 10 characters"),
        validators.Regexp(r'^[0-9]*', message = "Product ID can contain only digits")
    ))
    submit = SubmitField("Extract opinions")