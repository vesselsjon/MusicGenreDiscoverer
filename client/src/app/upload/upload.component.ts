import { Component } from '@angular/core';
import { MusicGenreDiscovererService } from '../services/music-genre-discoverer.service';

@Component({
  selector: 'app-upload',
  standalone: false,
  templateUrl: './upload.component.html',
  styleUrl: './upload.component.scss'
})
export class UploadComponent {
  recommendations: any[] = [];

  constructor(private musicGenreDiscovererService: MusicGenreDiscovererService) { }

  // This will be called when a user selects a file
  onFileUpload(event: any) {
    const formData = new FormData();
    formData.append('file', event.target.files[0]);

    this.musicGenreDiscovererService.Upload(formData).subscribe({
      next: (response) => {
        this.recommendations = response;
      },
      error: (error) => {
        console.error('Error uploading file:', error);
      }
    });
  }

  // You could use submitFile() to trigger other logic if needed.
  submitFile() {
    console.log('File submitted');
  }
}

