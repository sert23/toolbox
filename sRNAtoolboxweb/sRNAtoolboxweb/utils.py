from crispy_forms.layout import HTML, Div


def create_collapsable_div(*fields, **kwargs):
    title = kwargs['title']
    c_id = kwargs['c_id']
    extra = ''
    if 'extra_title' in kwargs:
        extra = kwargs['extra_title']
    panel_title = HTML('<h4 class="panel-title"><a data-toggle="collapse" href="#'+c_id+'">'+title+'</a>'+extra+'</h4>')
    panel_heading = Div(panel_title, css_class='panel-heading')
    form_group = Div(*fields, css_class='form-group')
    body = Div(form_group, css_class='panel-body')
    if 'open' in kwargs and kwargs['open']:
        collapse_in = "panel-collapse collapse in"
    else:
        collapse_in = "panel-collapse collapse"
    panel_collapse = Div(body, css_class=collapse_in, css_id=c_id)
    panel = Div(panel_heading, panel_collapse, css_class="panel panel-default")
    return panel


def render_modal(modal):
    return '<a  data-toggle="modal" data-target="#'+modal+'" class="btn btn-link"><i class="fa fa-question-circle"> </i></a>'