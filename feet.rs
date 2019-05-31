use std::env;
use std::fs;
use std::io;
use std::io::{Error, Write, stdout};
use std::path::Path;
use std::process::{Command, Stdio};


fn main() -> Result<(), Error> {
    let exec = std::env::current_exe()?;
    let exec_path = Path::new(&exec);
    let exec_name = exec_path.file_name().unwrap();
    let exec_base = exec_path.file_stem().unwrap().to_str().expect("cannot get file stem");
    let data_dir = format!("{}_data", exec_base);

    if Path::new("./feetmaker.py").exists() {
        println!("Do not run {:?} in its own source directory", exec_name);
        std::process::exit(1);
    }

    if Path::new(&data_dir).exists() {
        let mod_exec = Path::new(&exec_name).metadata()?.modified()?;
        let mod_runtime = Path::new(&data_dir).metadata()?.modified()?;

        if mod_exec > mod_runtime {
            fs::remove_dir_all(Path::new(&data_dir))?;
        }
    }

    if !Path::new(&data_dir).exists() {
        println!("Extracting the Python Feet Runtime... (one-time operation)");
        let file = fs::File::open(&exec_name).unwrap();
        let mut archive = zip::ZipArchive::new(file).unwrap();
        let total = archive.len();
        
        for i in 0..total {
            let mut file = archive.by_index(i).unwrap();
            let outpath = file.sanitized_name();

            if (&*file.name()).ends_with('/') {
                fs::create_dir_all(&outpath).unwrap();
            } else {
                if i % 100 == 0 && i != 0 {
                    println!(" {}% ", ((i as f64 / total as f64) * 100.0) as i32);
                } else if i != 0 {
                    print!(".");
                    stdout().flush()?;
                }
                if let Some(p) = outpath.parent() {
                    if !p.exists() {
                        fs::create_dir_all(&p).unwrap();
                    }
                }
                let mut outfile = fs::File::create(&outpath).unwrap();
                io::copy(&mut file, &mut outfile).unwrap();
            }

            // Get and Set permissions
            #[cfg(unix)]
            {
                use std::os::unix::fs::PermissionsExt;

                if let Some(mode) = file.unix_mode() {
                    fs::set_permissions(&outpath, fs::Permissions::from_mode(mode)).unwrap();
                }
            }
        }
        std::fs::rename("feet", &data_dir)?;
        println!(" done!");
    }

    // Next, if there is a requirements file, install that
    if Path::new("./requirements.txt").exists() && !Path::new("./Lib/").exists() {
        let script = &format!("{}/feet.py", data_dir);
        println!("Installing requirements... {}", script);
        let mut child = Command::new(format!("{}/cpython/python", data_dir))
            .args(&[script, "library", "--update"])
            .stderr(Stdio::inherit())
            .stdout(Stdio::inherit())
            .stdin(Stdio::inherit())
            .spawn()?;
        child.wait().expect("Invoking the Feet runtime script failed.");
    }

    // Now, runtime is either extracted or already was, so run the commands

    let mut args: Vec<String> = env::args().collect();
    args.remove(0);

    println!("{}/feet.py", data_dir);
    let mut child = Command::new(format!("{}/cpython/python", data_dir))
        .arg(format!("{}/feet.py", data_dir))
        .args(args)
        .stderr(Stdio::inherit())
        .stdout(Stdio::inherit())
        .stdin(Stdio::inherit())
        .spawn()?;

    child.wait().expect("Invoking the Feet runtime script failed.");
    Ok(())
}
