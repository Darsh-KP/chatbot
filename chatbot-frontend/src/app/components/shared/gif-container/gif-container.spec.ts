import { ComponentFixture, TestBed } from '@angular/core/testing';
import { GifContainer } from './gif-container';

describe('GifContainer', () => {
  let component: GifContainer;
  let fixture: ComponentFixture<GifContainer>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GifContainer],
    }).compileComponents();

    fixture = TestBed.createComponent(GifContainer);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
