#!/usr/bin/perl

use strict;
use utf8;
use CGI;
use CGI::Cookie;
use DBI;
use lib ('/home/takahashi/perl/local/lib/perl5');
use HTML::Template;
use HTML::Entities;
use Encode;
use Data::Dumper;
binmode (STDIN,  ':utf8');
binmode (STDOUT, ':utf8');

package Utils;

sub isValidEmail {
	my $user_name = shift;
	return length($user_name) <= 255 && $user_name =~ /^[!-~]+(@[!-~]+)?$/;
}

sub isValidUserPassword {
	my $password = shift;
	return $password =~ /^[!-~]{8,128}$/;
}

1;