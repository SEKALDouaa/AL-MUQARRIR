import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TranscriptionDetailComponent } from './transcription-detail.component';

describe('TranscriptionDetailComponent', () => {
  let component: TranscriptionDetailComponent;
  let fixture: ComponentFixture<TranscriptionDetailComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TranscriptionDetailComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TranscriptionDetailComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
