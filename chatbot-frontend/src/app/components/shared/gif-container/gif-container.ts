import { Component, computed, model } from '@angular/core';
import { getGifFilePath, ResponsePhase } from './ResponsePhase';

@Component({
  imports: [],
  selector: 'app-gif-container',
  styleUrl: './gif-container.css',
  templateUrl: './gif-container.html',
})
export class GifContainer {
  //Ask caller to provide response state for component
  phase = model.required<ResponsePhase>();

  //Compute the corresponding file path given the phase as an input
  gifPath =
    computed(() => getGifFilePath(this.phase()));
}
