from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse

import json
import plotly.express as px
from .models import Source, Income
from .forms import FilterDate
from userpreferences.models import UserPreference

# Create your views here.
@login_required(login_url='users:login')
def index(request):
    sources = Source.objects.all()
    income = Income.objects.filter(user=request.user)
    paginator = Paginator(income,2)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    currency = UserPreference.objects.get(user=request.user).currency
    context={
        'sources': sources,
        'income': income,
        'pages': page_obj,
        'currency': currency,
    }
    return render(request,'income/index.html', context)

@login_required(login_url='users:login')
def add_income(request):
    sources = Source.objects.all()
    context = {
        'sources':sources,  
        'values':request.POST
    }

    if request.method == 'POST':
        amount = request.POST['amount']
        description = request.POST['description']
        source = request.POST['source']
        date = request.POST['income_date']

        if not amount:
            messages.error(request,'Amount is required!')
            return render(request, 'income/add_income.html',context)
        
        Income.objects.create(user=request.user,amount=amount, source=source, description=description, date=date)
        messages.success(request, "Income saved successfully")
        return redirect('income:index')


    return render(request,'income/add_income.html',context)

def income_edit(request, pk ):
    income = get_object_or_404(Income, pk=pk)
    sources = Source.objects.all()
    context = {
        'income':income,
        'sources':sources
    }
    if request.method == 'POST':
        amount = request.POST['amount']
        description = request.POST['description']
        source = request.POST['source']
        date = request.POST['income_date']

        if not amount:
            messages.error(request,'Amount is required!')
            return render(request, 'income/edit_income.html',context)
        
        
        income.user=request.user
        income.amount=amount
        income.source=source
        income.description=description 
        income.date=date

        income.save()
        messages.success(request, "Income updated successfully")
        return redirect('income:index')

    return render(request,'income/edit_income.html', context)


def delete_income(request, pk):
    income = get_object_or_404(Income, pk=pk)
    income.delete()
    messages.warning(request, "Your Expenses has been deleted!")
    return redirect('income:index')
    

def search_param(request):
    if request.method == 'POST':
        search_str = json.loads(request.body).get('searchText') # transform into a python dict

        income = Income.objects.filter(
            user=request.user, amount__startswith = search_str
            ) |Income.objects.filter(
            user=request.user, source__icontains = search_str
            ) |Income.objects.filter(
            user=request.user, description__icontains = search_str
            ) |Income.objects.filter(
            user=request.user, date__startswith = search_str
            )
            
        data = income.values() # return dictionaries
        return JsonResponse(list(data), safe=False)
    

def summary_income(request):
    source_sum = Income.objects.values('source').annotate(total_income=Sum('amount',distinct=True)).filter(user=request.user)
    start= request.GET.get('start')
    end= request.GET.get('end')
    

    if start:
        source_sum = source_sum.filter(date__gte=start)
    if end:
        source_sum = source_sum.filter(date__lte=end)

    
    x= list(source_sum.values_list('source',flat=True))
    y= list(source_sum.values_list('total_income',flat=True))
    # text= [f"{sum:.0f}" for sum in y ]

    # fig = px.bar(
    #     x=x,
    #     y=y,
    #     text=text,
    #     title= 'Summary',
    #     labels={'x':'Category', 'y':'expenses'}
    # )
    # fig.update_layout(title={
    #     'font_size':22,
    #     'xanchor':'center',
    #     'x':0.5
    # })
    # fig.update_traces(textfont_size=12, textangle=0)


    # chart = fig.to_html()
    context = {'form':FilterDate, 'cat':list(x) , 'total':list(y)}
    return render(request, 'income/summary_income.html', context)