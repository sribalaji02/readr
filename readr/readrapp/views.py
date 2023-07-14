import re
import os
import requests 
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
import boto3
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
from langchain.document_loaders import PyPDFLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

os.environ["OPENAI_API_KEY"] = ""
client = boto3.client('dynamodb', region_name='', aws_access_key_id='', aws_secret_access_key='')
db = boto3.resource('dynamodb', region_name='', aws_access_key_id='', aws_secret_access_key='')

worklist = []

class Users ():
    hasLink = False
    username = ''
    index = None
    def __init__(self, email = '', password = ''):

        self.__email = email
        self.__password = password
    
    def set_gotbook (self, hasLink):
        self.hasLink = hasLink
    
    def get_gotbook (self):
        return self.hasLink    
    
    def set_bookindex (self, index):
        self.index = index
    
    def get_bookindex (self):
        return self.index
        
    def get_username (self):
        
        return self.username
    
    def get_email (self):
        
        return self.__email
        
    def validate (self):
        
        global client
        isValid = False
 
        table = db.Table('readr_users')
        response = table.get_item(Key={'email': f"{self.__email}"})
        item = response.get("Item", None)
        if item != None:
            db_pass = response['Item']['password']
            if self.__password == db_pass:
                self.username = response['Item']['username']
                isValid = True
                return isValid
            
            else:
                return isValid
        else:
            return isValid
    
    def readr (self) :
        
        table= db.Table('readr_users')
        response = table.get_item(Key={'email': f"{self.__email}",})
        item = response.get("Item", None) 
        if item != None:
            if response['Item']['username'] == self.username:
                return True
        else :
            return False
        
    def downloads(self):
        
        table = db.Table('readr_downloads')
        response = table.get_item(Key={'email': f"{self.__email}"})
        item = response.get("Item", None)
        if item != None:
            if response['Item']['email'] == self.__email:
                name = response['Item']['name']
                link = response['Item']['link']
            link_lists = []
            new_link_list = []
            for item in link:
                if item.startswith("1."):
                    link_lists.append(new_link_list)
                    new_link_list = []
                urls = re.findall(r'(https?://\S+)', item)
                new_link_list.extend(urls)
            link_lists.append(new_link_list)
            if link_lists[0] == []:
                link_lists.pop(0)
                
            return link_lists, name

def signup (request) :
    try:
        global client
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        
        client.put_item(
            TableName='readr_users',
            Item={
                    'email': {
                        'S': "{}".format(email),
                    },
                    'password': {
                        'S': "{}".format(password),
                    },
                    'username': {
                        "S": "{}".format(username),
                    }
                }
            )
        client.put_item(
            TableName='readr_downloads',
            Item={
                    'email': {
                        'S': "{}".format(email),
                    },
                    'name': {
                        'L': []
                    },
                    'link': {
                        'L': []
                    }
                }
            )
        
        return render(request, 'signup.html')
    
    except Exception:
        return render(request, 'signup.html')

def login (request) :

    return render(request, 'login.html')

def forgot_val(request):
    mail = request.POST['email']
    table = db.Table('readr_users')
    response = table.get_item(Key={'email': f"{mail}"})
    item = response.get("Item", None)
    if item != None:
        pwd=response['Item']['password']
        usn=response['Item']['username']
        sender_email = ""
        sender_password = ""
        recipient_email = mail
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = "Readr Password Reset"

        body = f"Hello {usn}, \nYour account password is, {pwd}\nHappy Reading!"
        message.attach(MIMEText(body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        return HttpResponseRedirect(reverse('login'))
    else:
        return render(request,'forgot.html')

def forgot(request):
    return render(request,'forgot.html')

def logout(request):
    
    name = request.POST.get('name')
    for i in worklist:
        if i.get_username() == name:
            worklist.remove(i)
            break
    return render(request, 'login.html')

def validate(request): 
    
    email = str(request.POST['email'])
    password = str(request.POST['password'])
    
    if worklist != []:
        for i in worklist:
            if i.get_email() == email:
                continue
            else:
                worklist.append(Users(email=email, password=password))
    else:
        worklist.append(Users(email=email, password=password))            
    print(len(worklist))
    for i in worklist:
        if i.get_email() == email:
            if i.validate() == True:
                name = i.get_username()
                return HttpResponseRedirect (reverse('home', kwargs={'name':name}))
            else:
                worklist.remove(i)
                return render (request, 'invalid.html')

def home (request, name) :
    
    for i in worklist:
        if i.get_username() == name:
            client.update_item(TableName='readr_cache',
                        Key={
                            'email': {
                                    'S': "{}".format(i.get_email()),
                            }
                        },
                        ExpressionAttributeNames={
                            '#I': 'isActive',
                        },
                        ExpressionAttributeValues={
                            ':i': {
                                'BOOL': False,
                            },
                        },
                        UpdateExpression='SET #I = :i',
                        ReturnValues="UPDATED_NEW"
                    )
        else:
            continue
    
    return render(request, 'home.html', {'name':name})

def readr (request, name) :
    name = request.POST.get('name')
    print(name)
    for i in worklist:
        if i.get_username() == name:
            if i.readr() == True:
                client.put_item(TableName='readr_cache', Item = {'email': {'S': "{}".format(i.get_email()),}, 'isActive': {'BOOL': True,},})
                cache_ret = client.scan(
                ExpressionAttributeNames={
                    '#E': 'email',
                    '#B': 'isActive',
                },
                ProjectionExpression='#E, #B',
                TableName='readr_cache',
                )
                client.update_item(TableName='readr_cache',
                    Key={
                        'email': {
                                'S': "{}".format(i.get_email()),
                        }
                    },
                    ExpressionAttributeNames={
                        '#I': 'isActive',
                    },
                    ExpressionAttributeValues={
                        ':i': {
                            'BOOL': True,
                        },
                    },
                    UpdateExpression='SET #I = :i',
                    ReturnValues="UPDATED_NEW"
                )
                print(cache_ret['Count'])                
                return render(request, 'readr.html', {'name':name})
            return render(request, 'readr.html', {'name':name})
        else:
            continue    
        
    return render(request, 'readr.html')

def downloads(request, name): 
    uname = request.POST.get('name')
    for i in worklist:
        if i.get_username() == uname:
            link_lists, name = i.downloads()
            return render(request, 'downloads.html', {'name':name, 'link':link_lists, 'uname':uname})
        else:
            continue
        
    return render(request, 'downloads.html', {'uname':uname})

def indexer (request, name) :
    uname = request.POST.get('name')
    for i in worklist:
        if i.get_username() == uname:
            i.set_gotbook(False)
            name = i.downloads()[1]
            return render(request, 'indexer.html', {'name':name, 'uname':uname})
        else:
            continue
        
    return render(request, 'indexer.html', {'uname':uname})

def chapterchat (request, name) :
    index = request.POST.get('index')
    name = request.POST.get('name', name)
    message = request.POST.get('message')
    chat_response = ""
    for i in worklist:
        if i.get_username() == name:
            if i.get_bookindex() == None:
                i.set_bookindex(index)
            if message != None:
                book_links = i.downloads()[0]
                book_link = book_links[int(i.get_bookindex()) - 1][2]
                print(book_link)
                if i.get_gotbook() == False:
                    i.set_gotbook(True)
                    url = str(book_link)
                    r = requests.get(url, allow_redirects=True)
                    open(f'{i.get_bookindex()}.pdf', 'wb').write(r.content)
                if i.get_bookindex() != None:
                    chat_response = get_ans(message, file_path=f"{i.get_bookindex()}.pdf", chain_type="refine", k=1)
            return render(request, 'chapterchat.html', {'name': name, 'chat_response': chat_response})
        else:
            continue
    return render(request, 'chapterchat.html', {'name': name, 'chat_response': chat_response})

def get_ans(message, file_path, chain_type, k):
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_documents(documents)
    embeddings = OpenAIEmbeddings()
    db = Chroma.from_documents(texts, embeddings)
    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": k})
    qa = RetrievalQA.from_chain_type(llm=OpenAI(), chain_type=chain_type, retriever=retriever, return_source_documents=True)
    result = qa({"query": message})
    
    return result["result"]