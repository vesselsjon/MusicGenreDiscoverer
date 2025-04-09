import { NgModule } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatToolbarModule } from '@angular/material/toolbar';

@NgModule({
  imports: [
    MatButtonModule,
    MatCardModule, 
    MatIconModule,
    MatProgressSpinnerModule,
    MatToolbarModule, 
  ],
  exports: [
    MatButtonModule,
    MatCardModule, 
    MatIconModule,
    MatProgressSpinnerModule,
    MatToolbarModule, 
  ],
})
export class MaterialModule { }