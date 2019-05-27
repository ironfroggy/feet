use std::env;
use std::process::{Command, Stdio};
use std::io::{BufRead, BufReader, Error, ErrorKind, Write, stdout};
// use std::io::Error;
use std::path::Path;
use std::io;
use std::fs;

use std::io::{Seek, Read};
use zip::result::ZipResult;
use zip::read::{ZipFile, ZipArchive};
// use zip::write::{FileOptions, ZipWriter};
use std::fs::File;

fn browse_zip_archive<T, F, U>(buf: &mut T, browse_func: F) -> ZipResult<Vec<U>>
    where T: Read + Seek,
          F: Fn(&ZipFile) -> ZipResult<U>
{
    let mut archive = ZipArchive::new(buf)?;
    (0..archive.len())
        .map(|i| archive.by_index(i).and_then(|file| browse_func(&file)))
        .collect()
}

fn main() -> Result<(), Error> {
    let mod_exec = fs::metadata("feet.exe")?.modified()?;
    let mod_runtime = fs::metadata("feet")?.modified()?;

    if (mod_exec > mod_runtime) {
        fs::remove_dir_all("./feet/");
    }

    if Path::new("./feetmaker.py").exists() {
        println!("Do not run feet.exe in its own source directory");
        std::process::exit(1);
    }

    if !Path::new("./feet/").exists() {
        print!("Extracting the Python Feet Runtime... (one-time operation)");
        let archive_path = "./feet.exe";
        let file = fs::File::open(&archive_path).unwrap();
        let mut archive = zip::ZipArchive::new(file).unwrap();
        let total = archive.len();
        
        for i in 0..total {
            let mut file = archive.by_index(i).unwrap();
            let outpath = file.sanitized_name();

            if (&*file.name()).ends_with('/') {
                fs::create_dir_all(&outpath).unwrap();
            } else {
                // println!("File {} extracted to \"{}\" ({} bytes)", i, outpath.as_path().display(), file.size());
                if i == 0 {
                    println!();
                } else if i % 100 == 0 {
                    println!(" {}/{}", i, total);
                } else {
                    print!(".");
                    stdout().flush();
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
    }

    // Next, if there is a requirements file, install that
    if Path::new("./requirements.txt").exists() && !Path::new("./Lib/").exists() {
        let mut child = Command::new("./feet/cpython/python")
            .args(&["./feet/feet.py", "library", "--update"])
            .stderr(Stdio::inherit())
            .stdout(Stdio::inherit())
            .stdin(Stdio::inherit())
            .spawn()?;
        child.wait();
    }

    // Now, runtime is either extracted or already was, so run the commands

    let mut args: Vec<String> = env::args().collect();
    args.remove(0);

    let mut child = Command::new("./feet/cpython/python")
        .arg("./feet/feet.py")
        .args(args)
        .stderr(Stdio::inherit())
        .stdout(Stdio::inherit())
        .stdin(Stdio::inherit())
        .spawn()?;

    child.wait();
    Ok(())
}
