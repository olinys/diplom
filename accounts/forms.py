from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile, Product, Category, PickupPoint, Subcategory, Camera, Memory, RAM, CoreCount, Color, ScreenDiagonal, BatteryCapacity, OperatingSystem, Processor, ConnectionType, ConnectorType

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


class UserLoginForm(AuthenticationForm):
    pass


class UserProfileForm(forms.ModelForm):
    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'phone_number', 'birth_date', 'gender', 'delivery_address', 'profile_picture']


from django import forms
from .models import Product, Subcategory

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'price', 'category', 'subcategory',
            'memory', 'ram', 'core_count', 'color', 'screen_diagonal',
            'battery_capacity', 'operating_system', 'main_camera', 'front_camera',
            'cpu_frequency', 'processor', 'connector_type', 'connection_type',
            'image', 'description', 'stock_quantity'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Динамическая загрузка подкатегорий
        self.fields['subcategory'].queryset = Subcategory.objects.none()

        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['subcategory'].queryset = Subcategory.objects.filter(category_id=category_id).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.category:
            self.fields['subcategory'].queryset = Subcategory.objects.filter(category=self.instance.category).order_by('name')

        # Загрузка значений для параметров
        self.fields['memory'].queryset = Memory.objects.all()
        self.fields['ram'].queryset = RAM.objects.all()
        self.fields['core_count'].queryset = CoreCount.objects.all()
        self.fields['color'].queryset = Color.objects.all()
        self.fields['screen_diagonal'].queryset = ScreenDiagonal.objects.all()
        self.fields['battery_capacity'].queryset = BatteryCapacity.objects.all()
        self.fields['operating_system'].queryset = OperatingSystem.objects.all()
        self.fields['main_camera'].queryset = Camera.objects.all()
        self.fields['front_camera'].queryset = Camera.objects.all()
        self.fields['processor'].queryset = Processor.objects.all()
        self.fields['connector_type'].queryset = ConnectorType.objects.all()
        self.fields['connection_type'].queryset = ConnectionType.objects.all()

        # Включение возможности добавления новых значений для параметров через Select2
        for field in ['memory', 'ram', 'core_count', 'color', 'screen_diagonal', 'battery_capacity', 
                      'operating_system', 'main_camera', 'front_camera', 'processor', 'connector_type', 'connection_type']:
            self.fields[field].widget.attrs.update({
                'class': 'select2',
                'data-placeholder': f"Выберите {self.fields[field].label.lower()}",
            })


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

class SubcategoryForm(forms.ModelForm):
    class Meta:
        model = Subcategory
        fields = ['name', 'category']  # Поля для названия подкатегории и выбора категории

    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=True,
        empty_label="Выберите категорию",
        widget=forms.Select(attrs={"class": "form-control"})
    )


from django import forms
from .models import PickupPoint
from datetime import datetime

class PickupPointForm(forms.ModelForm):
    class Meta:
        model = PickupPoint
        fields = ['name', 'address', 'monday_open', 'monday_close', 
                  'tuesday_open', 'tuesday_close', 'wednesday_open', 'wednesday_close',
                  'thursday_open', 'thursday_close', 'friday_open', 'friday_close',
                  'saturday_open', 'saturday_close', 'sunday_open', 'sunday_close']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Преобразуем время в строку в формате HH:MM, если время в строковом формате
        for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
            open_time_field = f'{day}_open'
            close_time_field = f'{day}_close'
            
            if self.instance:
                open_time = self.instance.__getattribute__(open_time_field)
                close_time = self.instance.__getattribute__(close_time_field)
                
                # Преобразуем строку в объект времени, если это необходимо
                if isinstance(open_time, str):
                    open_time = datetime.strptime(open_time, '%H:%M:%S').time()
                if isinstance(close_time, str):
                    close_time = datetime.strptime(close_time, '%H:%M:%S').time()
                
                # Преобразуем в строку времени в формате HH:MM
                self.fields[f'{day}_open'].initial = open_time.strftime('%H:%M')
                self.fields[f'{day}_close'].initial = close_time.strftime('%H:%M')
            else:
                # Если экземпляр не существует, устанавливаем значение по умолчанию
                self.fields[f'{day}_open'].initial = '09:00'
                self.fields[f'{day}_close'].initial = '21:00'
