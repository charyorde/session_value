from django import template
from django.conf import settings

register = template.Library()

@register.tag
def session_value(parser, token):
	"""
	For each template tag the template parser encounters, it calls a Python function with the tag
	contents and the parser object itself. This function is responsible for returning a Node 
	instance based on the contents of the tag.
	
	The main function of session_value is that it checks and parses the format of the
	command when been used.
	
	Make some template tags to be available to a particular view alone.

	If the view name of the current url is ..., get its session variable called 'consumer' 
	and parse it to get out its values. return a dict to do a dot reference on.
		- inside render, define the context to be the view name (probably its reverse name)
	
	For example, # arguments are the view name and session variable name.
	{% session_value [view_name] [session_variable] %} 

	Returns a dict or string (to be decided)

	"""
	bits = token.split_contents()
	if len(bits) < 2:
		raise TemplateSyntaxError("'%s' takes at least one argument"
                                  " (path to a view)" % bits[0])
	view_name = bits[1]
	session_variable = '' # or args - bits at session_variable
	kwargs = None # bits as argument to session_variable
	
	return EdupaySessionNode(view_name, session_variable, kwargs, legacy_view_name=True)
session_value = register.tag(session_value)
	
class SessionNode(template.Node):
	def __init__(self, view_name, session_variable, kwargs=None, legacy_view_name=True): #session_variable is used as args
		self.view_name = view_name
		self.session_variable = session_variable
		#self.args = args
		if kwargs is not None:
			self.kwargs = kwargs
		if not legacy_view_name:
			self.legacy_view_name = legacy_view_name
		
	def render(self, context):
		from django.core.urlresolvers import reverse, NoReverseMatch
		session_variable = [arg.resolve(context) for arg in self.session_variable]
		kwargs = 'institution_name' # a key from session_variable
		view_name = self.view_name
		if not self.legacy_view_name:
			view_name = view_name.resolve(context)
		url = ''
        try:
            url = reverse(view_name, args=session_variable, kwargs=kwargs, current_app=context.current_app)
        except NoReverseMatch, e:
            if settings.SETTINGS_MODULE:
                project_name = settings.SETTINGS_MODULE.split('.')[0]
                try:
                    url = reverse(project_name + '.' + view_name,
                              args=session_variable, kwargs=kwargs,
                              current_app=context.current_app)
                except NoReverseMatch:
					pass
		session_value = None
		# check the view_name if it exists
		# if it exists, look in the session object for session_variable
		# hint: inside HttpResponse, there's a context object and a context_instance of 
		# RequestContext type. Check in here for the session_variable. Alternatively,
		# use context[request].page to get the page_obj see: pagination tags
		# if it exists, check it's type
		# if its type is a dict, check if session_variable has another arg passed into it
		# if yes, use it as a key to look up the right value in the dict (session_variable)
		# if the type of the session_variable is a string, return the string
		return session_value
	