document.addEventListener('DOMContentLoaded', function() {
    // Предварительный просмотр загруженных файлов
    const fileInput = document.getElementById('file');
    const previewImage = document.getElementById('preview-image');
    const previewVideo = document.getElementById('preview-video');
    
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;
            
            // Проверяем тип файла
            if (file.type.startsWith('image/')) {
                // Файл является изображением
                previewImage.classList.remove('d-none');
                previewVideo.classList.add('d-none');
                
                // Отображаем изображение
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewImage.src = e.target.result;
                };
                reader.readAsDataURL(file);
            } else if (file.type.startsWith('video/')) {
                // Файл является видео
                previewImage.classList.add('d-none');
                previewVideo.classList.remove('d-none');
                
                // Отображаем видео
                const videoURL = URL.createObjectURL(file);
                previewVideo.src = videoURL;
            }
        });
    }
    
    // Подсветка опасных предметов при наведении
    const dangerItems = document.querySelectorAll('.list-group-item');
    if (dangerItems.length) {
        dangerItems.forEach(item => {
            item.addEventListener('mouseenter', function() {
                this.classList.add('bg-danger', 'text-white');
            });
            
            item.addEventListener('mouseleave', function() {
                this.classList.remove('bg-danger', 'text-white');
            });
        });
    }
});