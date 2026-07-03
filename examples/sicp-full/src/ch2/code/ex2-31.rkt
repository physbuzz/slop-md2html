#lang sicp

(define (square x) (* x x))
(define (tree-map f tree)
  (if  (not (pair? tree)) 
    (f tree)
    (map (lambda (tree2) (tree-map f tree2)) 
         tree)))

(define (square-tree tree) 
  (tree-map square tree))

(define examp (list 1 2 
                (list (list 3 4 5) 
                      (list 7 8 9) 
                      (list (list 10 11))) 
                (list 12 13)))
(square-tree examp)
(display "More advanced thingy: ")
(newline)
;; Cool example showing more advanced stuff (symbol literal!)
(tree-map (lambda (x) `(f ,x)) examp)
