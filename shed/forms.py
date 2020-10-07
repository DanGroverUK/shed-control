from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired, Length

class FanForm(FlaskForm):
    hours = SelectField('Hours:', choices=["0", "1", "2", "3", "4", "5"], coerce=int, validators=[DataRequired()])
    mins = SelectField('Minutes:', choices=["0", "15", "30", "45"], coerce=int, validators=[DataRequired()])
    add = SubmitField('Add')
    off = SubmitField('Turn Off')
    refresh = SubmitField('Refresh')
