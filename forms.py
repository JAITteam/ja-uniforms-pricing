from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.fields import SelectField   
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileField, FileAllowed

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class StyleSearchForm(FlaskForm):
   vendor_style = StringField('Vendor Style Code', validators=[DataRequired()], 
                            render_kw={"placeholder": "Enter style code (e.g., 21324-3202)"})
   submit = SubmitField('Search Style')

