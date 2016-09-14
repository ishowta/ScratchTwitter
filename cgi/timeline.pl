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
require 'utils.cgi';

#need [{id, user_id, mail, text, time},...] , $user_id
sub makeTimeLine {
	my ($data, $user_id) = @_;

	# Config
	my $TIMELINE_TMPL_PATH = '../tmpl/timeline.tmpl';

	# Load tmpl
		my $timeline_tmpl = HTML::Template->new(
		filename => $TIMELINE_TMPL_PATH,
		utf8 => 1
	);

	# Put Tweet
	my @tweets = ();
	foreach my $raw_tweet (@$data){
		my %tweet = (	'USER_URL' => '<a href="userpage.cgi?user_id='.$raw_tweet->{'user_id'}.'">'.$raw_tweet->{'mail'}.'</a>',
						'TEXT'      => $raw_tweet->{'text'},
						'TIME'      => $raw_tweet->{'time'}
					);
		if($raw_tweet->{'user_id'} eq $user_id){
			$tweet{'ERASE_TWEET_ZONE'} = '<a href="delete.cgi?id='.$raw_tweet->{'id'}.'" class="close"><span class="glyphicon glyphicon-remove text-danger"></span></a>';
		}
		push @tweets, \%tweet;
	}
	$timeline_tmpl->param('TIMELINE_LOOP' => \@tweets);

	return $timeline_tmpl;
}

1;
