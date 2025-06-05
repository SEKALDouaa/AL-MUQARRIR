import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PvDetailComponent } from './pv-detail.component';

describe('PvDetailComponent', () => {
  let component: PvDetailComponent;
  let fixture: ComponentFixture<PvDetailComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PvDetailComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PvDetailComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
