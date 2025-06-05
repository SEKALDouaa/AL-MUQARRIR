import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AnalysisDetailComponent } from './analysis-detail.component';

describe('AnalysisDetailComponent', () => {
  let component: AnalysisDetailComponent;
  let fixture: ComponentFixture<AnalysisDetailComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AnalysisDetailComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AnalysisDetailComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
