open Ast
open Distribution

let max_depth = Sys.argv.(3) |> int_of_string

let random_seed state = 
  Random.State.bits state

(** Generates a random integer literal. *)
let random_int_lit state =
  let n = Random.State.bits64 state in
  IntLit n

(** Generates a random leaf (terminal) of the AST. *)
let random_terminal state p = 
  choose_normalized state [
    X;
    Y;

    random_int_lit state;
    
    True;
    False;
  ] [ p.x_p; p.y_p; p.int_lit_p; p.true_p; p.false_p ]

(** Generates a random node (non-terminal) of the AST. *)
let rec random_expr (state: Random.State.t) (depth: int) (p: expr_p) =
  choose_normalized state [
    lazy X;
    lazy Y;

    lazy (random_int_lit state);

    lazy (Neg (random_expr_child state depth p));
    lazy (Plus (random_expr_child state depth p, random_expr_child state depth p));
    lazy (Minus (random_expr_child state depth p, random_expr_child state depth p));
    lazy (Times (random_expr_child state depth p, random_expr_child state depth p));

    lazy True;
    lazy False;

    lazy (Not (random_expr_child state depth p));

    lazy (LessThan (random_expr_child state depth p, random_expr_child state depth p));
    lazy (LessEqual (random_expr_child state depth p, random_expr_child state depth p));
    lazy (GreaterThan (random_expr_child state depth p, random_expr_child state depth p));
    lazy (GreaterEqual (random_expr_child state depth p, random_expr_child state depth p));
    lazy (Equal (random_expr_child state depth p, random_expr_child state depth p));
    lazy (NotEqual (random_expr_child state depth p, random_expr_child state depth p));

    lazy (BitwiseAnd (random_expr_child state depth p, random_expr_child state depth p));
    lazy (BitwiseOr (random_expr_child state depth p, random_expr_child state depth p));
    lazy (BitwiseComplement (random_expr_child state depth p));
    lazy (BitwiseXor (random_expr_child state depth p, random_expr_child state depth p));
    lazy (LeftShift (random_expr_child state depth p, random_expr_child state depth p));
    lazy (RightShift (random_expr_child state depth p, random_expr_child state depth p));
  ] [ p.x_p; p.y_p; p.int_lit_p; 
      p.neg_p; p.plus_p; p.minus_p; p.times_p; 
      p.true_p; p.false_p; p.not_p; 
      p.less_than_p; p.less_equal_p; 
      p.greater_than_p; p.greater_equal_p; 
      p.equal_p; p.not_equal_p; 
      p.bitwise_and_p; p.bitwise_or_p; p.bitwise_complement_p; 
      p.bitwise_xor_p; p.left_shift_p; p.right_shift_p ]

and random_expr_child state depth p =
  let seed = random_seed state in
  let state = Random.State.make [|seed|] in 
  if depth >= max_depth then 
    random_terminal state p
  else
    Lazy.force (random_expr state (depth + 1) p)
