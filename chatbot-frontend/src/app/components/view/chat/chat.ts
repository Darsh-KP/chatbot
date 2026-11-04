import { Component } from '@angular/core';
import { MatMiniFabButton } from '@angular/material/button';
import { MatIcon } from '@angular/material/icon';
import { CdkTextareaAutosize } from '@angular/cdk/text-field';

@Component({
  imports: [MatMiniFabButton, MatIcon, CdkTextareaAutosize],
  selector: 'app-chat',
  styleUrl: './chat.css',
  templateUrl: './chat.html',
})
export class Chat {}
