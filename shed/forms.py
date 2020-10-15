from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired


class FanForm(FlaskForm):
    fhours = SelectField('Hours:', choices=["0", "1", "2", "3",
                                           "4", "5"], coerce=int, validators=[DataRequired()])
    fmins = SelectField('Minutes:', choices=["0", "15", "30",
                                            "45"], coerce=int, validators=[DataRequired()])
    fadd = SubmitField('Add')
    foff = SubmitField('Turn Off')
    frefresh = SubmitField('Refresh')


class LightForm(FlaskForm):
    lon = SubmitField('Turn On')
    loff = SubmitField('Turn Off')
