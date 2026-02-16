use keyring::Entry;
use std::env;

fn usage() {
    eprintln!("usage: vas_keyring <set|get|delete> <service> <account> [secret]");
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 4 {
        usage();
        std::process::exit(2);
    }

    let cmd = &args[1];
    let service = &args[2];
    let account = &args[3];
    let entry = Entry::new(service, account).expect("invalid keyring params");

    match cmd.as_str() {
        "set" => {
            if args.len() != 5 {
                usage();
                std::process::exit(2);
            }
            let secret = &args[4];
            if let Err(err) = entry.set_password(secret) {
                eprintln!("keyring_set_failed:{err}");
                std::process::exit(1);
            }
            println!("ok");
        }
        "get" => match entry.get_password() {
            Ok(secret) => println!("{secret}"),
            Err(err) => {
                eprintln!("keyring_get_failed:{err}");
                std::process::exit(1);
            }
        },
        "delete" => {
            if let Err(err) = entry.delete_password() {
                eprintln!("keyring_delete_failed:{err}");
                std::process::exit(1);
            }
            println!("ok");
        }
        _ => {
            usage();
            std::process::exit(2);
        }
    }
}
