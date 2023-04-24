open Ast
open Generator

let () = 
  Random.self_init ();
  let seed = Random.bits () in
  print_endline ("SEED: " ^ string_of_int seed);
  let distribution = random_distribution seed in
  print_endline (string_of_expr (random_ast seed 0 distribution))