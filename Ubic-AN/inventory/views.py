from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Plano, Activo
import json

def map_view(request):
    planos = Plano.objects.all()
    # PENDING: We should serialize the assets unassigned and assigned
    activos_sin_asignar = Activo.objects.filter(plano__isnull=True)
    
    # We serialize the assigned ones safely passing only needed data
    activos_asignados = Activo.objects.filter(plano__isnull=False)
    
    context = {
        'planos': planos,
        'activos_sin_asignar': activos_sin_asignar,
        'activos_asignados': activos_asignados,
    }
    return render(request, 'inventory/index.html', context)

@csrf_exempt
def save_asset_position(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            activo_id = data.get('activo_id')
            plano_id = data.get('plano_id')
            coord_x = data.get('x')
            coord_y = data.get('y')

            activo = Activo.objects.get(id=activo_id)
            plano = Plano.objects.get(id=plano_id)
            
            activo.plano = plano
            activo.coord_x = coord_x
            activo.coord_y = coord_y
            activo.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'invalid method'}, status=405)

@csrf_exempt
def unassign_asset(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            activo_id = data.get('activo_id')
            activo = Activo.objects.get(id=activo_id)
            activo.plano = None
            activo.coord_x = None
            activo.coord_y = None
            activo.save()
            return JsonResponse({'status': 'success'})
        except Activo.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Activo no encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'invalid method'}, status=405)

