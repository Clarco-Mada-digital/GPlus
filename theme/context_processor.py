def theme(request):
  return ({
      'is_dark_theme': request.session['is_dark_theme']
  } if 'is_dark_theme' in request.session else {
      'is_dark_theme': True
  })
