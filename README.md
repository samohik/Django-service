# Django-service  
## Instructions:  
```pip install -r requirements.txt```  
```cd social_web```  
```python manage.py makemigrations```  
```python manage.py migrate```  
```python manage.py test```  
```python manage.py createsuperuser```  
```python manage.py runserver```

## Paths:
- `/swagger` - Documentation  
- `/registration` 
  - `post` - Create a new user  
- `/friends`   
  - `get` - View a user's list of friends.  
- `/friends/<int:id>`
  - `get` - Get a user friend status with some other user.  
  - `delete` - Remove a user from another user from their friends.  
- `/requests` 
  - `get` - View to the user a list of their outgoing and incoming friend requests.  
  - `post` - Sends a friend request and works out according to the situation.  
- `/requests/<int:id>`
  - `get` - Status check with user.   
  - `post` - Accept or reject a user's friend request from another user.  