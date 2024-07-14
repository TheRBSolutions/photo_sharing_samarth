# mypy: ignore-missing-imports
from django.http import HttpResponse
from django.shortcuts import redirect
from .models import *

def unauthenticated_user(view_func):
	def wrapper_func(request, *args, **kwargs):
		if request.user.is_authenticated:
			return redirect('photographer_dashboard')
		else:
			return view_func(request, *args, **kwargs)

	return wrapper_func

def allowed_users(allowed_roles=[]):
	def decorator(view_func):
		def wrapper_func(request, *args, **kwargs):

			group = None
			if request.user.groups.exists():
				group = request.user.groups.all()[0].name

			if group in allowed_roles:
				return view_func(request, *args, **kwargs)
			else:
				return HttpResponse('You are not authorized to view this page')
		return wrapper_func
	return decorator

def admin_only(view_func):
	def wrapper_function(request, *args, **kwargs):
		user = request.user
		
	
		group = None
		if request.user.groups.exists():
			group = request.user.groups.all()[0].name

		if group == 'user':
			return redirect('user-page')

		if group == 'photographer':
			user = request.user
			username = user.username
			# if admin_user_settings_instance.is_money_paid:
       
			return view_func(request, *args, **kwargs)
			# else:
			# 	return HttpResponse(
            #         f"Hi {username} \n Please do the pending payment in order to use the software."
            #     )

	return wrapper_function




