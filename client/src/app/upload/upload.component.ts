import { Component } from '@angular/core';
import { MusicGenreDiscovererService } from '../services/music-genre-discoverer.service';

@Component({
  selector: 'app-upload',
  standalone: false,
  templateUrl: './upload.component.html',
  styleUrls: ['./upload.component.scss']
})
export class UploadComponent {
  //#region Inputs, Outputs, ViewChilds
  //#endregion Inputs, Outputs, ViewChilds

  //#region Public Variables
  public Recommendations: any[] = [];
  public IsUploading: boolean = false;
  //#endregion Public Variables

  //#region Private Variables
  //#endregion Private Variables

  //#region Properties
  //#endregion Properties

  //#region Constructor and Angular Life Cycle
  constructor(private musicGenreDiscovererService: MusicGenreDiscovererService) { }
  //#endregion Constructor and Angular Life Cycle

  //#region Event Handlers
  public OnFileUpload(event: any) {
    const formData = new FormData();
    formData.append('file', event.target.files[0]);

    this.IsUploading = true;  // Show spinner
    this.musicGenreDiscovererService.Upload(formData).subscribe({
      next: (response) => {
        this.IsUploading = false;
        this.Recommendations = response;  // Show recommendations
      },
      error: (error) => {
        this.IsUploading = false;
        console.error('Error uploading file:', error);
      }
    });
  }
  //#endregion Event Handlers

  //#region Public Methods
  //#endregion Public Methods

  //#region Private Methods
  //#endregion Private Methods
}
