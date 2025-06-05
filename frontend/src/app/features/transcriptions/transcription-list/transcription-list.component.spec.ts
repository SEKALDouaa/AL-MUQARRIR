import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TranscriptionListComponent } from './transcription-list.component';

describe('TranscriptionListComponent', () => {
  let component: TranscriptionListComponent;
  let fixture: ComponentFixture<TranscriptionListComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TranscriptionListComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TranscriptionListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
