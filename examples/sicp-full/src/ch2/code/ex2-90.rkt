#lang sicp

(define pi 3.14159)
(define (square x) (* x x))
(define (accumulate op initial sequence)
  (if (null? sequence)
      initial
      (op (car sequence)
          (accumulate op
                      initial
                      (cdr sequence)))))
;; Define a map-indexed function. (map-indexed f '(a b c)) is
;; ((f a 0) (f b 1) (f c 2))
(define (map-indexed my-lambda lst)
  (define (map-indexed-inner lst-cur counter)
    (if (null? lst-cur) '()
    (cons (my-lambda (car lst-cur) counter) (map-indexed-inner (cdr lst-cur) (+ counter 1)))))
  (map-indexed-inner lst 0))
;; get and put definitions
(define operation-table '())

(define (assoc key records)
  (cond ((null? records) #f)
        ((equal? key (caar records)) (car records))
        (else (assoc key (cdr records)))))

(define (assoc-op key records)
   (cond ((null? records) #f)
         ((equal? key (caar records)) (car records))
         (else (assoc-op key (cdr records)))))

(define (put op type-tags proc)
  (let ((op-list-entry (assoc-op op operation-table)))
    (if op-list-entry
        (let ((proc-list (cadr op-list-entry)))
           (let ((proc-pair-entry (assoc type-tags proc-list)))
             (if proc-pair-entry
                 (set-cdr! proc-pair-entry proc)
                 (set-car! (cdr op-list-entry)
                           (cons (cons type-tags proc) proc-list)))))
        (set! operation-table
              (cons (list op (list (cons type-tags proc)))
                    operation-table)))))

(define (get op type-tags)
  (let ((op-list-entry (assoc-op op operation-table)))
    (if op-list-entry
        (let ((proc-list (cadr op-list-entry)))
          (let ((proc-pair-entry (assoc type-tags proc-list)))
            (if proc-pair-entry
                (cdr proc-pair-entry)
                #f)))
        #f)))

;; Modified for ex2-78. 
(define (attach-tag type-tag contents)
  (if (equal? type-tag 'scheme-number) 
      contents
      (cons type-tag contents)))
(define (type-tag datum)
  (cond ((pair? datum) (car datum))
        ((number? datum) 'scheme-number)
        (else (error "Bad tagged datum: TYPE-TAG" datum))))
(define (contents datum)
  (cond ((pair? datum) (cdr datum))
        ((number? datum) datum)
        (else (error "Bad tagged datum: CONTENTS" datum))))
(define (apply-generic op . args)
  (let ((type-tags (map type-tag args)))
    (let ((proc (get op type-tags)))
      (if proc
          (apply proc (map contents args))
          (error
            "No method for these types: APPLY-GENERIC"
            (list op type-tags))))))


;; Number package
(define (install-scheme-number-package)
  (define (tag x)
    (attach-tag 'scheme-number x))
  (put 'add '(scheme-number scheme-number)
       (lambda (x y) (tag (+ x y))))
  (put 'sub '(scheme-number scheme-number)
       (lambda (x y) (tag (- x y))))
  (put 'mul '(scheme-number scheme-number)
       (lambda (x y) (tag (* x y))))
  (put 'div '(scheme-number scheme-number)
       (lambda (x y) (tag (/ x y))))
  (put 'make 'scheme-number
       (lambda (x) (tag x)))
  (put '=zero? '(scheme-number)
       (lambda (x) (= x 0)))
  (put 'negate '(scheme-number)
       (lambda (x) (- x)))
  'done)

(install-scheme-number-package)

(define (make-scheme-number n)
  ((get 'make 'scheme-number) n))

;; ===================================================================
;; ======================== Rational package =========================
;; ===================================================================

(define (install-rational-package)
  ;; internal procedures
  (define (numer x) (car x))
  (define (denom x) (cdr x))
  (define (make-rat n d)
    (let ((g (gcd n d)))
      (cons (/ n g) (/ d g))))
  (define (add-rat x y)
    (make-rat (+ (* (numer x) (denom y))
                 (* (numer y) (denom x)))
              (* (denom x) (denom y))))
  (define (sub-rat x y)
    (make-rat (- (* (numer x) (denom y))
                 (* (numer y) (denom x)))
              (* (denom x) (denom y))))
  (define (mul-rat x y)
    (make-rat (* (numer x) (numer y))
              (* (denom x) (denom y))))
  (define (div-rat x y)
    (make-rat (* (numer x) (denom y))
              (* (denom x) (numer y))))

  ;; z1a/z1b = z2a/z2b  iff z1a*z2b - z2a*z1b = 0
  ;; equ? for problem 2.79
  (define (equ? z1 z2)
    (= (- (* (numer z1) (denom z2))
          (* (numer z2) (denom z1)))
        0))
  ;; interface to rest of the system
  (put 'equ? '(rational rational) equ?)
  (define (tag x) (attach-tag 'rational x))
  (put 'add '(rational rational)
       (lambda (x y) (tag (add-rat x y))))
  (put 'sub '(rational rational)
       (lambda (x y) (tag (sub-rat x y))))
  (put 'mul '(rational rational)
       (lambda (x y) (tag (mul-rat x y))))
  (put 'div '(rational rational)
       (lambda (x y) (tag (div-rat x y))))
  (put 'make 'rational
       (lambda (n d) (tag (make-rat n d))))
  ;problem 2.80
  (put '=zero? '(rational)
    (lambda (a) (= (numer a) 0)))
  (put 'negate '(rational)
       (lambda (r) (tag (make-rat (- (numer r)) (denom r)))))
  'done)

(install-rational-package)

(define (make-rational n d)
  ((get 'make 'rational) n d))

;; ===================================================================
;; ================= Complex polar and rectangular ===================
;; ===================================================================

(define (install-polar-package)
  ;; internal procedures
  (define (magnitude z) (car z))
  (define (angle z) (cdr z))
  (define (make-from-mag-ang r a) (cons r a))
  (define (real-part z)
    (* (magnitude z) (cos (angle z))))
  (define (imag-part z)
    (* (magnitude z) (sin (angle z))))
  (define (make-from-real-imag x y)
    (cons (sqrt (+ (square x) (square y)))
          (atan y x)))
  ;; interface to the rest of the system
  (define (tag x) (attach-tag 'polar x))
  (put 'real-part '(polar) real-part)
  (put 'imag-part '(polar) imag-part)
  (put 'magnitude '(polar) magnitude)
  (put 'angle '(polar) angle)
  (put 'make-from-real-imag 'polar
       (lambda (x y) 
         (tag (make-from-real-imag x y))))
  (put 'make-from-mag-ang 'polar
       (lambda (r a) 
         (tag (make-from-mag-ang r a))))
  (put 'negate '(polar)
       (lambda (z) (tag (make-from-mag-ang (magnitude z) (+ (angle z) pi)))))
  'done)
(install-polar-package)

(define (install-rectangular-package)
  ;; internal procedures
  (define (real-part z) (car z))
  (define (imag-part z) (cdr z))
  (define (make-from-real-imag x y)
    (cons x y))
  (define (magnitude z)
    (sqrt (+ (square (real-part z))
             (square (imag-part z)))))
  (define (angle z)
    (atan (imag-part z) (real-part z)))
  (define (make-from-mag-ang r a)
    (cons (* r (cos a)) (* r (sin a))))
  ;; interface to the rest of the system
  (define (tag x)
    (attach-tag 'rectangular x))
  (put 'real-part '(rectangular) real-part)
  (put 'imag-part '(rectangular) imag-part)
  (put 'magnitude '(rectangular) magnitude)
  (put 'angle '(rectangular) angle)
  (put 'make-from-real-imag 'rectangular
       (lambda (x y)
         (tag (make-from-real-imag x y))))
  (put 'make-from-mag-ang 'rectangular
       (lambda (r a)
         (tag (make-from-mag-ang r a))))
  (put 'negate '(rectangular)
       (lambda (z) (tag (make-from-real-imag (- (real-part z) (- (imag-part z)))))))
  'done)
(install-rectangular-package)

;; ===================================================================
;; ========================= Complex package =========================
;; ===================================================================

(define (install-complex-package)
  ;; imported procedures from rectangular 
  ;; and polar packages
  (define (real-part z)
    (apply-generic 'real-part z))
  (define (imag-part z)
    (apply-generic 'imag-part z))
  (define (magnitude z)
    (apply-generic 'magnitude z))
  (define (angle z)
    (apply-generic 'angle z))

  (define (make-from-real-imag x y)
    ((get 'make-from-real-imag 
          'rectangular) 
     x y))
  (define (make-from-mag-ang r a)
    ((get 'make-from-mag-ang 'polar) 
     r a))
  ;; internal procedures
  (define (add-complex z1 z2)
    (make-from-real-imag 
     (+ (real-part z1) (real-part z2))
     (+ (imag-part z1) (imag-part z2))))
  (define (sub-complex z1 z2)
    (make-from-real-imag 
     (- (real-part z1) (real-part z2))
     (- (imag-part z1) (imag-part z2))))
  (define (mul-complex z1 z2)
    (make-from-mag-ang 
     (* (magnitude z1) (magnitude z2))
     (+ (angle z1) (angle z2))))
  (define (div-complex z1 z2)
    (make-from-mag-ang 
     (/ (magnitude z1) (magnitude z2))
     (- (angle z1) (angle z2))))

  (define (equ? z1 z2) ; for problem 2.79
    (and (= (real-part z1) (real-part z2)) 
         (= (imag-part z1) (imag-part z2))))
  ;; interface to rest of the system
  (put 'equ? '(complex complex) equ?)
  (put 'real-part '(complex) real-part) ; Changes from problem 2.77
  (put 'imag-part '(complex) imag-part)
  (put 'magnitude '(complex) magnitude)
  (put 'angle '(complex) angle)
  (put 'negate '(complex)
       (lambda (z) (tag (apply-generic 'negate z))))

  (define (tag z) (attach-tag 'complex z))
  (put 'add '(complex complex)
       (lambda (z1 z2) 
         (tag (add-complex z1 z2))))
  (put 'sub '(complex complex)
       (lambda (z1 z2) 
         (tag (sub-complex z1 z2))))
  (put 'mul '(complex complex)
       (lambda (z1 z2) 
         (tag (mul-complex z1 z2))))
  (put 'div '(complex complex)
       (lambda (z1 z2) 
         (tag (div-complex z1 z2))))
  (put 'make-from-real-imag 'complex
       (lambda (x y) 
         (tag (make-from-real-imag x y))))
  (put 'make-from-mag-ang 'complex
       (lambda (r a) 
         (tag (make-from-mag-ang r a))))
  ;problem 2.80
  (put '=zero? '(complex)
    (lambda (z) (and (= (real-part z) 0) (= (imag-part z) 0))))
  'done)

(install-complex-package)

(define (=zero? a)
  (apply-generic '=zero? a))
(define (real-part z)
  (apply-generic 'real-part z))
(define (imag-part z)
  (apply-generic 'imag-part z))
(define (magnitude z)
  (apply-generic 'magnitude z))
(define (angle z)
  (apply-generic 'angle z))
(define (mul a b)
  (apply-generic 'mul a b))
(define (add a b)
  (apply-generic 'add a b))
(define (sub a b)
  (apply-generic 'sub a b))
(define (equ? a b)
  (apply-generic 'equ? a b))


(define (install-sparse-polynomial-package)
  ;; internal procedures
  ;; representation of poly
  (define (make-poly variable term-list)
    (cons variable term-list))
  (define (variable p) (car p))
  (define (term-list p) (cdr p))

  (define (variable? x) (symbol? x))
  (define (same-variable? v1 v2)
    (and (variable? v1)
         (variable? v2)
         (eq? v1 v2)))

  (define (mul-terms L1 L2)
    (if (empty-termlist? L1)
      (the-empty-termlist)
      (add-terms
       (mul-term-by-all-terms
        (first-term L1) L2)
       (mul-terms (rest-terms L1) L2))))

  (define (mul-term-by-all-terms t1 L)
    (if (empty-termlist? L)
      (the-empty-termlist)
      (let ((t2 (first-term L)))
        (adjoin-term
         (make-term
          (+ (order t1) (order t2))
          (mul (coeff t1) (coeff t2)))
         (mul-term-by-all-terms
          t1
          (rest-terms L))))))


  ;; representation of terms and term lists
  (define (adjoin-term term term-list)
    (if (=zero? (coeff term))
      term-list
      (cons term term-list)))
  (define (the-empty-termlist) '())
  (define (first-term term-list) (car term-list))
  (define (rest-terms term-list) (cdr term-list))
  (define (empty-termlist? term-list)
    (null? term-list))
  (define (make-term order coeff)
    (list order coeff))
  (define (order term) (car term))
  (define (coeff term) (cadr term))


  (define (add-poly p1 p2)
    (if (same-variable? (variable p1)
                        (variable p2))
      (make-poly
       (variable p1)
       (add-terms (term-list p1)
                  (term-list p2)))
      (error "Polys not in same var:
             ADD-POLY"
             (list p1 p2))))

  (define (mul-poly p1 p2)
    (if (same-variable? (variable p1)
                        (variable p2))
      (make-poly
       (variable p1)
       (mul-terms (term-list p1)
                  (term-list p2)))
      (error "Polys not in same var:
             MUL-POLY"
             (list p1 p2))))

  (define (add-terms L1 L2)
    (cond ((empty-termlist? L1) L2)
      ((empty-termlist? L2) L1)
      (else
       (let ((t1 (first-term L1))
             (t2 (first-term L2)))
         (cond ((> (order t1) (order t2))
                (adjoin-term
                 t1
                 (add-terms (rest-terms L1)
                            L2)))
           ((< (order t1) (order t2))
            (adjoin-term
             t2
             (add-terms
              L1
              (rest-terms L2))))
           (else
            (adjoin-term
             (make-term
              (order t1)
              (add (coeff t1)
                   (coeff t2)))
             (add-terms
              (rest-terms L1)
              (rest-terms L2)))))))))
  ;; During construction, we don't check whether coefficients are zero
  ;; So now, we have to check all coefficients.
  (define (=zero?-poly poly)
    (accumulate (lambda (x y) (and y (=zero? (coeff x))))
                #t
                (term-list poly)))
  ;; Make sure to install the function
  (put '=zero? '(sparse-poly) =zero?-poly)

  ;; Exercise 2-88
  (define (negate-terms L) 
    (if (empty-termlist? L)
      L
      (let ((t (first-term L)) (r (rest-terms L)))
        (adjoin-term (make-term (order t) (apply-generic 'negate (coeff t)))
                     (negate-terms r)))))
  (define (sub-terms L1 L2)
    (add-terms L1 (negate-terms L2)))
  (define (sub-poly p1 p2)
    (if (same-variable? (variable p1)
                        (variable p2))
      (make-poly
       (variable p1)
       (sub-terms (term-list p1)
                  (term-list p2)))
      (error "Polys not in same var:
             SUB-POLY"
             (list p1 p2))))
  (put 'sub '(sparse-poly sparse-poly)
       (lambda (p1 p2) 
         (tag (sub-poly p1 p2))))
  (put 'negate '(sparse-poly)
       (lambda (p) 
         (tag (make-poly (variable p) (negate-terms (term-list p))))))
  ;; interface to rest of the system
  (define (tag p) (attach-tag 'sparse-poly p))
  (put 'add '(sparse-poly sparse-poly)
       (lambda (p1 p2) 
         (tag (add-poly p1 p2))))
  (put 'mul '(sparse-poly sparse-poly)
       (lambda (p1 p2) 
         (tag (mul-poly p1 p2))))
  (put 'make 'sparse-poly
       (lambda (var terms) 
         (tag (make-poly var terms))))
  'done)
(define (install-dense-polynomial-package)
  ;; internal procedures
  ;; representation of poly
  ;; Chop off the leading zeros of a term list.
  (define (chop-leading-zeros L)
    (cond ((null? L) L)
          ((apply-generic '=zero? (car L)) (chop-leading-zeros (cdr L)))
          (else L)))
  (define (make-poly variable term-list)
    (cons variable (chop-leading-zeros term-list)))
  (define (variable p) (car p))
  (define (term-list p) (cdr p))

  (define (variable? x) (symbol? x))
  (define (same-variable? v1 v2)
    (and (variable? v1)
         (variable? v2)
         (eq? v1 v2)))


  ;; Note: this is NOT generic. We could define a ((get 'make-zero type)) 
  ;; to make it generic.
  (define (make-zero-terms l)
    (if (= l 0) '() (cons 0 (make-zero-terms (- l 1)))))
  ;; returns the term list representing 
  ;; (coeff)*(variable)^order * (polynomial represented by L)
  (define (mul-term-by-all-terms order coeff L)
    (if (null? L)
      '()
      (append (map (lambda (x) 
                     (apply-generic 'mul x coeff)) 
                   L)  
              (make-zero-terms order))))
  (define (mul-terms L1 L2)
    (let ((length1 (length L1)) (length2 (length L2)))
      (cond ((< length1 length2) (mul-terms L2 L1))
            ((= length2 0) '())
            (else 
              (accumulate 
                (lambda (Lx Ly) (add-terms Lx Ly))
                '()
                (map-indexed 
                  (lambda (coeff ctr) 
                    ;; multiply L2 polynomial by the term x*(var)^(order).
                    (mul-term-by-all-terms (- (- length1 ctr) 1) coeff L2))
                  L1))))))

  (define (empty-termlist? term-list)
    (null? term-list))

  (define (mul-poly p1 p2)
    (if (same-variable? (variable p1)
                        (variable p2))
      (make-poly
       (variable p1)
       (mul-terms (term-list p1)
                  (term-list p2)))
      (error "Polys not in same var:
             MUL-POLY"
             (list p1 p2))))

  (define (add-terms L1 L2)
    (let ((length1 (length L1)) (length2 (length L2)))
      (cond ((< length1 length2) (add-terms L2 L1))
            ((= length1 length2) 
              (map (lambda (x y) 
                     (apply-generic 'add x y)) 
                   L1 
                   L2))
            (else (cons (car L1) (add-terms (cdr L1) L2))))))
  (define (add-poly p1 p2)
    (if (same-variable? (variable p1)
                        (variable p2))
      (make-poly
       (variable p1)
       (add-terms (term-list p1)
                  (term-list p2)))
      (error "Polys not in same var:
             ADD-POLY"
             (list p1 p2))))

  (define (=zero?-poly poly)
    (accumulate (lambda (x y) (and y (=zero? x)))
                #t
                (term-list poly)))


  (define (negate-terms L) 
    (map (lambda (x) (apply-generic 'negate x)) L))
  (define (sub-terms L1 L2)
    (add-terms L1 (negate-terms L2)))
  (define (sub-poly p1 p2)
    (if (same-variable? (variable p1)
                        (variable p2))
      (make-poly
       (variable p1)
       (sub-terms (term-list p1)
                  (term-list p2)))
      (error "Polys not in same var:
             SUB-POLY"
             (list p1 p2))))
  ;; interface to rest of the system
  (define (tag p) (attach-tag 'dense-poly p))
  (put 'add '(dense-poly dense-poly)
       (lambda (p1 p2) 
         (tag (add-poly p1 p2))))
  (put 'mul '(dense-poly dense-poly)
       (lambda (p1 p2) 
         (tag (mul-poly p1 p2))))
  (put 'make 'dense-poly
       (lambda (var terms) 
         (tag (make-poly var terms))))
  (put 'sub '(dense-poly dense-poly)
       (lambda (p1 p2) 
         (tag (sub-poly p1 p2))))
  (put 'negate '(dense-poly)
       (lambda (p) 
         (tag (make-poly (variable p) (negate-terms (term-list p))))))
  (put '=zero? '(dense-poly) =zero?-poly)
  'done)

(define (install-polynomial-package)
  (define (tag p) (attach-tag 'polynomial p))
  (put '=zero? '(polynomial)
       (lambda (p) (apply-generic '=zero? p)))
  (put 'negate '(polynomial)
       (lambda (p) (tag (apply-generic 'negate p))))
  (put 'make-sparse-polynomial 'polynomial
       (lambda (var terms) 
         (tag ((get 'make 'sparse-poly) var terms))))
  (put 'make-dense-polynomial 'polynomial
       (lambda (var terms) 
         (tag ((get 'make 'dense-poly) var terms))))
  (define (dense-poly->sparse-poly dense)
    (let ((var (car dense)) 
          (terms (cdr dense)) 
          (order (length (cdr dense))))
      ((get 'make 'sparse-poly) 
          var 
          (map-indexed (lambda (term index) (list (- (- order index) 1) term)) terms))))
  (define (put-poly-symb symb)
    (put symb '(polynomial polynomial)
         (lambda (p1 p2) 
           (tag 
             (let ((t1 (type-tag p1)) (t2 (type-tag p2)))
               (cond ((eq? t1 t2) (apply-generic symb p1 p2))
                     ((and (eq? t1 'sparse-poly)
                           (eq? t2 'dense-poly)) 
                      (apply-generic symb p1 (dense-poly->sparse-poly (contents p2))))
                     ((and (eq? t1 'dense-poly)
                           (eq? t2 'sparse-poly)) 
                      (apply-generic symb (dense-poly->sparse-poly (contents p1)) p2))
                     (else (error "Symbol called with polynomials of invalid types:" symb t1 t2))))))))
  (put-poly-symb 'add)
  (put-poly-symb 'mul)
  (put-poly-symb 'sub))

(install-sparse-polynomial-package)
(install-dense-polynomial-package)
(install-polynomial-package)

(define (make-dense-polynomial var terms)
  ((get 'make-dense-polynomial 'polynomial) var terms))
(define (make-sparse-polynomial var terms)
  ((get 'make-sparse-polynomial 'polynomial) var terms))

(define a (make-dense-polynomial 'x '(1 1 1 1)))
(define b (make-dense-polynomial 'x '(1 -1)))
(define c (make-sparse-polynomial 'x '((3 1) (2 1) (1 1) (0 1))))
(define d (make-sparse-polynomial 'x '((1 1) (0 -1))))

(display "dense-dense (x^3+x^2+x+1)+(x-1) = ")
(apply-generic 'add a b)
(display "dense-dense (x^3+x^2+x+1)*(x-1) = ")
(apply-generic 'mul a b)

(display "sparse-sparse (x^3+x^2+x+1)+(x-1) = ")
(apply-generic 'add c d)
(display "sparse-sparse (x^3+x^2+x+1)*(x-1) = ")
(apply-generic 'mul c d)

(display "dense-sparse (x^3+x^2+x+1)+(x-1) = ")
(apply-generic 'add a d)
(display "sparse-dense (x^3+x^2+x+1)*(x-1) = ")
(apply-generic 'mul c b)

