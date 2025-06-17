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
  public Artist: string = '';
  public IsUploading: boolean = false;
  public Recommendations: any[] = [];
  public SelectedFile: File | null = null;
  public SongName: string = '';
  public YouTubeSearchUrl: string = '';
  //#endregion Public Variables

  //#region Private Variables
  //#endregion Private Variables

  //#region Properties
  //#endregion Properties

  //#region Constructor and Angular Life Cycle
  constructor(private musicGenreDiscovererService: MusicGenreDiscovererService) { }
  //#endregion Constructor and Angular Life Cycle

  //#region Event Handlers
  public OnFileSelected(event: any) {
    if (event.target.files.length > 0) {
      this.SelectedFile = event.target.files[0];
    }
  }
  //#endregion Event Handlers

  //#region Public Methods
  public Submit() {
    if (!this.SelectedFile) return;

    const formData = new FormData();
    formData.append('file', this.SelectedFile);
    formData.append('song_name', this.SongName || this.SelectedFile.name);
    formData.append('artist', this.Artist || 'Unknown Artist');

    this.IsUploading = true;
    this.musicGenreDiscovererService.Upload(formData).subscribe({
      next: (response) => {
        this.IsUploading = false;
        this.Recommendations = response.map((rec: any) => ({
          ...rec,
          youtubeLink: `https://www.youtube.com/results?search_query=${encodeURIComponent(rec.song_name + ' ' + rec.artist)}`
        }));
      },
      error: (error) => {
        this.IsUploading = false;
        console.error('Upload failed:', error);
      }
    });
  }
  //#endregion Public Methods

  //#region Private Methods
  //#endregion Private Methods
}
