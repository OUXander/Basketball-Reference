all: serve

# use Gunicorn as proper Flask app server
serve:
	gunicorn --chdir app/ main:app
