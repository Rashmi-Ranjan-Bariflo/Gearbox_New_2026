import json
import csv
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import gear_value
from django.http import JsonResponse
from django.utils.timezone import now, make_aware
from datetime import datetime
from datetime import timedelta
from gearapp.models import gear_value



@csrf_exempt
def gear_value_view(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            value_val = body.get('value', '')

            # Return all entries
            all_data = gear_value.objects.all().order_by('date', 'time')
            result = [
                {
                    'date': data.date.isoformat(),
                    'time': data.time.strftime('%H:%M:%S'),
                    'value': data.value
                }
                for data in all_data
            ]
            return JsonResponse(result, safe=False, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    elif request.method == 'GET':
        all_data = gear_value.objects.all().order_by('date', 'time')
        result = [
            {
                'date': data.date.isoformat(),
                'time': data.time.strftime('%H:%M:%S'),
                'value': data.value
            }
            for data in all_data
        ]
        return JsonResponse(result, safe=False)

    return JsonResponse({'error': 'Only GET and POST allowed'}, status=405)



@csrf_exempt
def filter_gear_value(request):
    if request.method == 'GET':
        from_date_str = request.GET.get('from_date')
        to_date_str = request.GET.get('to_date')
        print(from_date_str,to_date_str)


        if not from_date_str or not to_date_str:
            return JsonResponse({'error': 'Both "from_date" and "to_date" are required.'}, status=400)

        try:
            start = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            print("111111111")
            end = datetime.strptime(to_date_str, '%Y-%m-%d').date()
            print("2222222")
        except ValueError:
            return JsonResponse({'error': 'Invalid date format. Use yyyy-MM-dd.'}, status=400)

        values = gear_value.objects.filter(date__gte=start, date__lte=end).order_by('date', 'time')

        if not values.exists():
            return JsonResponse({'error': 'No data found for the selected date range.'}, status=404)

        result = [
            {
                'date': item.date.isoformat(),
                'time': item.time.strftime('%H:%M:%S'),
                'value': item.value 
            }
            for item in values
        ]

        return JsonResponse(result, safe=False)

    return JsonResponse({'error': 'Only GET allowed'}, status=405)


@csrf_exempt
def download_gear_value(request):
    if request.method == 'GET':
        # Get all gear values ordered by datetime
        all_data = gear_value.objects.all().order_by('-date', '-time')

        #latest time when the last data before stop
        if not all_data.exists():
            return JsonResponse({'error': 'No gear value data found.'}, status=404)

        # Get the most recent timestamp before machine stop
        last_item = all_data.first()
        stop_time = make_aware(datetime.combine(last_item.date, last_item.time))

        # Define the time range: 10 minutes before the machain stop
        start_time = stop_time - timedelta(minutes=10)

        # Filter data within this 10m 
        filtered = []
        for item in all_data:
            item_datetime = make_aware(datetime.combine(item.date, item.time))
            if start_time <= item_datetime <= stop_time:
                filtered.append((item.date, item.time, item.value))

        filtered.sort(key=lambda x: datetime.combine(x[0], x[1]))

        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="gear_values_before_stop.csv"'

        writer = csv.writer(response)
        writer.writerow(['Date', 'Time', 'Value'])

        for date, time, value in filtered:
            writer.writerow([date.isoformat(), time.strftime('%H:%M:%S'), value])

        return response

    return JsonResponse({'error': 'Only GET allowed'}, status=405)
