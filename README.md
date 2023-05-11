# Django-service  

## Instructions:  
```pip install -r requirements.txt```  
```cd social_web```  
```python manage.py makemigrations```  
```python manage.py migrate```  
```python manage.py test```  
```python manage.py createsuperuser```  
```python manage.py runserver```  

### or using Docker:  
```sudo docker-compose build```  
```sudo docker-compose up```  

## Paths :
- `/swagger` - Documentation  
- `/api/registration` 
  - `post` - Create a new user  
- `/api/friends`   
  - `get` - View a user's list of friends.  
- `/api/friends/<int:id>`
  - `get` - Get a user friend status with some other user.  
  - `delete` - Remove a user from another user from their friends.  
- `/api/requests` 
  - `get` - View to the user a list of their outgoing and incoming friend requests.  
  - `post` - Sends a friend request and works out according to the situation.  
- `/api/requests/<int:id>`
  - `get` - Status check with user.   
  - `post` - Accept or reject a user's friend request from another user.  
